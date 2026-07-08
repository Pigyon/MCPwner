"""FastAPI factory for DAST scanners that need custom execution/parsing.

Mirrors ``common.base_service.create_scanner_app`` but accepts a custom
``execute_scan`` callable instead of a CLI command builder, so wrappers that
need to parse stdout/logs/SQLite can do so before writing the JSON report.
"""

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List

from common.models import HealthResponse, ScanRequest, VersionResponse
from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)


def create_dast_app(
    tool_name: str,
    version_cmd: List[str],
    execute_scan: Callable[[ScanRequest, Path, int], None],
    tool_category: str = "dast",
) -> FastAPI:
    """Create a FastAPI app that runs a custom DAST scan function."""
    app = FastAPI(title=f"{tool_name.capitalize()} Service", version="1.0.0")

    _version_cache: Dict[str, str] = {}

    @app.get("/health", response_model=HealthResponse)
    def health():
        return {"status": "healthy", "service": tool_name}

    @app.get("/version", response_model=VersionResponse)
    def version():
        if "value" in _version_cache:
            return {"version": _version_cache["value"], "status": "success"}
        try:
            result = subprocess.run(
                version_cmd,
                capture_output=True,
                text=True,
                timeout=20,
                check=True,
            )
            _version_cache["value"] = result.stdout.strip() or result.stderr.strip()
            return {"version": _version_cache["value"], "status": "success"}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    def _resolve_report_dir(workspace_path: str, report_base: str = None) -> Path:
        if report_base:
            return Path(report_base) / "reports" / tool_category / tool_name
        parts = Path(workspace_path).parts
        if "workspaces" in parts:
            idx = parts.index("workspaces")
            if idx + 1 < len(parts):
                return Path(*parts[: idx + 2]) / "reports" / tool_category / tool_name
        return Path(workspace_path).parent / "reports" / tool_category / tool_name

    @app.post("/scan")
    def scan(request: ScanRequest):
        try:
            full_scan_path = Path(request.workspace_path) / request.scan_path
            if not full_scan_path.exists():
                raise HTTPException(
                    status_code=404, detail=f"Scan path does not exist: {full_scan_path}"
                )

            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
            output_dir = _resolve_report_dir(request.workspace_path, request.report_base)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{timestamp}.json"

            timeout_seconds = (request.config or {}).get("timeout_seconds", 600)
            try:
                execute_scan(request, output_path, timeout_seconds)
            except subprocess.TimeoutExpired as exc:
                logger.error("%s scan timed out after %ss", tool_name, timeout_seconds)
                stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
                return {
                    "status": "error",
                    "error": f"Scan timed out after {timeout_seconds}s",
                    "output": stdout,
                }
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

            if not output_path.exists():
                with open(output_path, "w", encoding="utf-8") as handle:
                    json.dump([], handle)

            finding_count = 0
            try:
                with open(output_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                    if isinstance(data, list):
                        finding_count = len(data)
                    elif isinstance(data, dict):
                        finding_count = len(data.get("results", [])) or 1
            except Exception as exc:
                logger.warning("Could not parse finding count from %s: %s", output_path, exc)

            return {
                "status": "success",
                "finding_count": finding_count,
                "report_path": str(output_path),
                "timestamp": timestamp,
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Scan execution error")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/reports")
    def list_reports(workspace_path: str, report_base: str = None):
        report_dir = _resolve_report_dir(workspace_path, report_base)
        if not report_dir.exists():
            return {"status": "success", "reports": []}
        reports = sorted(
            [path.stem for path in report_dir.iterdir() if path.is_file()],
            reverse=True,
        )
        return {"status": "success", "reports": reports}

    @app.get("/report/{timestamp}")
    def get_report(timestamp: str, workspace_path: str, report_base: str = None):
        report_dir = _resolve_report_dir(workspace_path, report_base)
        for ext in ("json",):
            candidate = report_dir / f"{timestamp}.{ext}"
            if candidate.exists():
                with open(candidate, encoding="utf-8") as handle:
                    data = json.load(handle)
                return {"status": "success", "report": data, "report_path": str(candidate)}
        raise HTTPException(
            status_code=404,
            detail=f"No report found for timestamp '{timestamp}' in {report_dir}",
        )

    return app
