import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List

from common.models import HealthResponse, ScanRequest, VersionResponse
from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)


def create_scanner_app(
    tool_name: str,
    version_cmd: List[str],
    scan_cmd_builder: Callable[[ScanRequest, Path], List[str]],
    report_format: str = "sarif",
    tool_category: str = "sast",
) -> FastAPI:
    """
    Create a FastAPI app for a SAST scanner.

    Args:
        tool_name: Name of the tool (e.g., "semgrep")
        version_cmd: Command to get version (e.g., ["semgrep", "--version"])
        scan_cmd_builder: Function that takes request and output path and returns command list
        report_format: Format of the report file extension (default: "sarif")
        tool_category: Category of the tool (default: "sast")
    """
    app = FastAPI(title=f"{tool_name.capitalize()} Service", version="1.0.0")

    @app.get("/health", response_model=HealthResponse)
    def health():
        """Health check endpoint."""
        return {"status": "healthy", "service": tool_name}

    @app.get("/version", response_model=VersionResponse)
    def version():
        """Get tool version."""
        try:
            result = subprocess.run(
                version_cmd,
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            return {"version": result.stdout.strip(), "status": "success"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/scan")
    def scan(request: ScanRequest):
        """
        Execute scan on a workspace.
        """
        try:
            # Build full scan path
            full_scan_path = Path(request.workspace_path) / request.scan_path

            if not full_scan_path.exists():
                raise HTTPException(
                    status_code=404, detail=f"Scan path does not exist: {full_scan_path}"
                )

            # Create output directory
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"

            # Determine report output directory.
            # If report_base is provided (e.g. for local_path workspaces), use it directly.
            if request.report_base:
                output_dir = Path(request.report_base) / "reports" / tool_category / tool_name
            else:
                workspace_base = Path(request.workspace_path).parent
                # Handle case where workspace path might be deeper or different
                # We want /workspaces/{id}/reports/sast/{tool}
                # Assuming request.workspace_path is /workspaces/{id} or /workspaces/{id}/source

                # Simple heuristic: find 'reports' sibling or child
                if "reports" in str(full_scan_path):
                    # Already inside a structure with reports? Unlikely for source
                    pass

                # Standard MCPwner structure: /workspaces/{id}/source -> /workspaces/{id}/reports
                # If workspace_path is /workspaces/{id}, then reports is /workspaces/{id}/reports
                # If workspace_path is /workspaces/{id}/source, then reports is /workspaces/{id}/reports

                # Let's assume standard structure where reports is at workspace root
                # We need to find the workspace root.
                # If path contains /workspaces/<id>, we can extract it.

                parts = Path(request.workspace_path).parts
                if "workspaces" in parts:
                    idx = parts.index("workspaces")
                    if idx + 1 < len(parts):
                        workspace_root = Path(*parts[: idx + 2])
                        output_dir = workspace_root / "reports" / tool_category / tool_name
                    else:
                        # Fallback
                        output_dir = Path(request.workspace_path) / "reports" / tool_category / tool_name
                else:
                    # Fallback for local testing etc
                    output_dir = (
                        Path(request.workspace_path).parent / "reports" / tool_category / tool_name
                    )

            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{timestamp}.{report_format}"

            # Build command
            try:
                cmd = scan_cmd_builder(request, output_path)
            except ValueError as e:
                logger.error(f"Scan configuration error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                # Other errors
                logger.error(f"Error building scan command: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to build scan command: {e}")

            # Execute scan
            logger.info(f"Executing {tool_name} scan: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,  # Don't raise on non-zero exit code as scanners often return 1 for findings
            )

            # Check if report was created
            if not output_path.exists():
                logger.error(f"Scan failed: {result.stderr}")
                # Some tools (e.g. arjun) don't write output when they find nothing.
                # If the tool exited cleanly (rc 0) and stderr is empty, treat as 0 findings.
                if result.returncode == 0 and not result.stderr.strip():
                    logger.info(
                        f"{tool_name} exited cleanly but produced no report — writing empty result"
                    )
                    with open(output_path, "w") as f:
                        json.dump([], f)
                else:
                    return {
                        "status": "error",
                        "error": f"Scan failed to generate report. Stderr: {result.stderr}",
                        "output": result.stdout,
                    }

            # Parse report for finding count (simple heuristic or JSON parse)
            finding_count = 0
            try:
                if report_format == "sarif":
                    with open(output_path, "r") as f:
                        data = json.load(f)
                        for run in data.get("runs", []):
                            finding_count += len(run.get("results", []))
                elif report_format == "json":
                    with open(output_path, "r") as f:
                        try:
                            data = json.load(f)
                            if isinstance(data, list):
                                finding_count = len(data)
                            elif isinstance(data, dict):
                                # Single JSON object (e.g. one httpx NDJSON line) = 1 finding
                                finding_count = len(data["results"]) if "results" in data else 1
                        except json.JSONDecodeError:
                            # Handle NDJSON (Newline Delimited JSON)
                            f.seek(0)
                            lines = [line for line in f.readlines() if line.strip()]
                            finding_count = len(lines)
                            # Convert NDJSON to JSON Array for easier consumption
                            try:
                                json_array = [json.loads(line) for line in lines]
                                with open(output_path, "w") as fw:
                                    json.dump(json_array, fw, indent=2)
                            except Exception as e:
                                logger.warning(f"Failed to convert NDJSON to JSON array: {e}")

            except Exception as e:
                logger.warning(f"Could not parse finding count from {output_path}: {e}")

            return {
                "status": "success",
                "finding_count": finding_count,
                "report_path": str(output_path),
                "timestamp": timestamp,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Scan execution error")
            raise HTTPException(status_code=500, detail=str(e))

    # ------------------------------------------------------------------
    # Report retrieval endpoints
    # ------------------------------------------------------------------

    def _resolve_report_dir(workspace_path: str, report_base: str = None) -> Path:
        """Resolve the report directory for this tool given a workspace path."""
        if report_base:
            return Path(report_base) / "reports" / tool_category / tool_name
        parts = Path(workspace_path).parts
        if "workspaces" in parts:
            idx = parts.index("workspaces")
            if idx + 1 < len(parts):
                return Path(*parts[: idx + 2]) / "reports" / tool_category / tool_name
        return Path(workspace_path).parent / "reports" / tool_category / tool_name

    @app.get("/reports")
    def list_reports(workspace_path: str, report_base: str = None):
        """List all available report timestamps for this tool."""
        report_dir = _resolve_report_dir(workspace_path, report_base)
        if not report_dir.exists():
            return {"status": "success", "reports": []}
        reports = sorted(
            [f.stem for f in report_dir.iterdir() if f.is_file()],
            reverse=True,
        )
        return {"status": "success", "reports": reports}

    @app.get("/report/{timestamp}")
    def get_report(timestamp: str, workspace_path: str, report_base: str = None):
        """Retrieve the full contents of a scan report by its timestamp."""
        report_dir = _resolve_report_dir(workspace_path, report_base)
        # Try known extensions
        for ext in (report_format, "json", "sarif"):
            candidate = report_dir / f"{timestamp}.{ext}"
            if candidate.exists():
                try:
                    with open(candidate) as f:
                        data = json.load(f)
                    return {"status": "success", "report": data, "report_path": str(candidate)}
                except json.JSONDecodeError:
                    # Return raw text if not valid JSON
                    with open(candidate) as f:
                        raw = f.read()
                    return {"status": "success", "report_raw": raw, "report_path": str(candidate)}
        raise HTTPException(
            status_code=404,
            detail=f"No report found for timestamp '{timestamp}' in {report_dir}",
        )

    return app
