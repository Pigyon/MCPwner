import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from common.models import HealthResponse, ScanRequest, VersionResponse

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
                raise HTTPException(status_code=404, detail=f"Scan path does not exist: {full_scan_path}")

            # Create output directory
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
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
                    workspace_root = Path(*parts[:idx+2])
                    output_dir = workspace_root / "reports" / tool_category / tool_name
                else:
                    # Fallback
                    output_dir = Path(request.workspace_path) / "reports" / tool_category / tool_name
            else:
                 # Fallback for local testing etc
                 output_dir = Path(request.workspace_path).parent / "reports" / tool_category / tool_name

            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{timestamp}.{report_format}"

            # Build command
            cmd = scan_cmd_builder(request, output_path)

            # Execute scan
            logger.info(f"Executing {tool_name} scan: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False  # Don't raise on non-zero exit code as scanners often return 1 for findings
            )

            # Check if report was created
            if not output_path.exists():
                logger.error(f"Scan failed: {result.stderr}")
                return {
                    "status": "error",
                    "error": f"Scan failed to generate report. Stderr: {result.stderr}",
                    "output": result.stdout
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
                        data = json.load(f)
                        # Tool specific parsing would be needed here for exact count
                        # But for now we just return success
                        if isinstance(data, list):
                            finding_count = len(data)
                        elif isinstance(data, dict) and "results" in data:
                            finding_count = len(data["results"])
            except Exception:
                logger.warning(f"Could not parse finding count from {output_path}")

            return {
                "status": "success",
                "finding_count": finding_count,
                "report_path": str(output_path),
                "timestamp": timestamp
            }

        except Exception as e:
            logger.exception("Scan execution error")
            raise HTTPException(status_code=500, detail=str(e))

    return app
