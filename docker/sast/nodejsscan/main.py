import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from common.models import HealthResponse, ScanRequest, VersionResponse
from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)

app = FastAPI(title="NodeJsScan Service", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy", "service": "nodejsscan"}


@app.get("/version", response_model=VersionResponse)
def version():
    try:
        result = subprocess.run(
            ["nodejsscan", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        ver = result.stdout.strip() or result.stderr.strip()
        return {"version": ver, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan")
def scan(request: ScanRequest):
    try:
        full_scan_path = Path(request.workspace_path) / request.scan_path

        if not full_scan_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Scan path does not exist: {full_scan_path}",
            )

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        parts = Path(request.workspace_path).parts
        if "workspaces" in parts:
            idx = parts.index("workspaces")
            if idx + 1 < len(parts):
                workspace_root = Path(*parts[: idx + 2])
                output_dir = workspace_root / "reports" / "sast" / "nodejsscan"
            else:
                output_dir = Path(request.workspace_path) / "reports" / "sast" / "nodejsscan"
        else:
            output_dir = Path(request.workspace_path).parent / "reports" / "sast" / "nodejsscan"

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}.json"

        # nodejsscan CLI: positional path arg, --json for JSON output
        cmd = ["nodejsscan", "--json", "-o", str(output_path), str(full_scan_path)]

        logger.info(f"Executing nodejsscan: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if not output_path.exists():
            return {
                "status": "error",
                "error": f"nodejsscan failed to generate report. Stderr: {result.stderr}",
                "output": result.stdout,
            }

        # nodejsscan JSON structure:
        # {"nodejs": {"rule_id": {"files": [...], "metadata": {...}}}, "templates": {...}}
        # Count total files across all rules in both nodejs and templates sections
        finding_count = 0
        try:
            with open(output_path) as f:
                data = json.load(f)
            for section in ("nodejs", "templates"):
                for rule_data in data.get(section, {}).values():
                    finding_count += len(rule_data.get("files", []))
        except Exception as e:
            logger.warning(f"Could not parse finding count: {e}")

        return {
            "status": "success",
            "finding_count": finding_count,
            "report_path": str(output_path),
            "timestamp": timestamp,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("NodeJsScan scan error")
        raise HTTPException(status_code=500, detail=str(e))


def _resolve_report_dir(workspace_path: str) -> Path:
    """Resolve the report directory for nodejsscan given a workspace path."""
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2]) / "reports" / "sast" / "nodejsscan"
    return Path(workspace_path).parent / "reports" / "sast" / "nodejsscan"


@app.get("/reports")
def list_reports(workspace_path: str):
    """List all available report timestamps for nodejsscan."""
    report_dir = _resolve_report_dir(workspace_path)
    if not report_dir.exists():
        return {"status": "success", "reports": []}
    reports = sorted(
        [f.stem for f in report_dir.iterdir() if f.is_file()],
        reverse=True,
    )
    return {"status": "success", "reports": reports}


@app.get("/report/{timestamp}")
def get_report(timestamp: str, workspace_path: str):
    """Retrieve the full contents of a nodejsscan report by its timestamp."""
    report_dir = _resolve_report_dir(workspace_path)
    for ext in ("json", "sarif"):
        candidate = report_dir / f"{timestamp}.{ext}"
        if candidate.exists():
            try:
                with open(candidate) as f:
                    data = json.load(f)
                return {"status": "success", "report": data, "report_path": str(candidate)}
            except json.JSONDecodeError:
                with open(candidate) as f:
                    raw = f.read()
                return {"status": "success", "report_raw": raw, "report_path": str(candidate)}
    raise HTTPException(
        status_code=404,
        detail=f"No report found for timestamp '{timestamp}' in {report_dir}",
    )
