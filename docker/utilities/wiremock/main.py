"""
WireMock Adapter Service

Wraps WireMock's admin API in MCPwner's standard HTTP interface.
WireMock runs internally on port 8080; this FastAPI adapter listens on port 8130.

The LLM uses this to:
  1. Register malicious/unexpected stub responses against third-party API endpoints
     discovered in source code (payment gateways, OAuth providers, microservices).
  2. Send test requests that trigger those stubs.
  3. Retrieve a JSON report describing all configured stubs and test outcomes.

Config options (passed via ScanRequest.config):
  stubs:         list of WireMock stub definition dicts (request/response mappings)
  test_requests: list of paths (relative to target) to GET after registering stubs
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WIREMOCK_ADMIN = "http://localhost:8080/__admin"
TOOL_NAME = "wiremock"
TOOL_CATEGORY = "utilities"

app = FastAPI(title="WireMock Adapter Service", version="1.0.0")


class ScanRequest(BaseModel):
    workspace_path: str
    scan_path: Optional[str] = "."
    config: Optional[Dict[str, Any]] = None
    report_base: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str


class VersionResponse(BaseModel):
    version: str
    status: str


def _report_dir(workspace_path: str, report_base: Optional[str] = None) -> Path:
    if report_base:
        return Path(report_base) / "reports" / TOOL_CATEGORY / TOOL_NAME
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2]) / "reports" / TOOL_CATEGORY / TOOL_NAME
    return Path(workspace_path).parent / "reports" / TOOL_CATEGORY / TOOL_NAME


def _wiremock_ready() -> bool:
    try:
        r = requests.get(f"{WIREMOCK_ADMIN}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": TOOL_NAME}


@app.get("/version", response_model=VersionResponse)
def version():
    """Return WireMock version from its admin API."""
    try:
        r = requests.get(f"{WIREMOCK_ADMIN}/version", timeout=5)
        r.raise_for_status()
        return {"version": r.json().get("version", "unknown"), "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan")
def scan(request: ScanRequest):
    """
    Register WireMock stubs and execute test requests against them.

    Workflow:
      1. Reset existing WireMock stubs.
      2. Register each stub from config['stubs'].
      3. Send GET requests to each path in config['test_requests'] via the mock server.
      4. Collect WireMock request journal to record what was triggered.
      5. Write JSON report to workspace.
    """
    try:
        if not _wiremock_ready():
            raise HTTPException(status_code=503, detail="WireMock is not ready yet")

        cfg = request.config or {}
        target: str = cfg.get("target", "")
        stubs: List[Dict] = cfg.get("stubs", [])
        test_paths: List[str] = cfg.get("test_requests", [])

        if not target:
            raise HTTPException(status_code=400, detail="config.target is required")

        requests.post(f"{WIREMOCK_ADMIN}/reset", timeout=5)

        registered = []
        for stub in stubs:
            r = requests.post(f"{WIREMOCK_ADMIN}/mappings", json=stub, timeout=5)
            if r.ok:
                registered.append(r.json())
            else:
                logger.warning(f"Failed to register stub: {r.text}")

        test_results = []
        base = target.rstrip("/")
        for path in test_paths:
            url = f"{base}{path}" if path.startswith("/") else f"{base}/{path}"
            try:
                resp = requests.get(
                    url,
                    proxies={"http": "http://localhost:8080", "https": "http://localhost:8080"},
                    timeout=10,
                    verify=False,
                )
                test_results.append(
                    {"url": url, "status_code": resp.status_code, "body_snippet": resp.text[:500]}
                )
            except Exception as e:
                test_results.append({"url": url, "error": str(e)})

        journal_resp = requests.get(f"{WIREMOCK_ADMIN}/requests", timeout=5)
        journal = journal_resp.json() if journal_resp.ok else {}

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        output_dir = _report_dir(request.workspace_path, request.report_base)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}.json"

        report = {
            "target": target,
            "stubs_registered": len(registered),
            "stubs": registered,
            "test_requests": test_results,
            "request_journal": journal.get("requests", []),
        }
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return {
            "status": "success",
            "finding_count": len(registered),
            "report_path": str(output_path),
            "timestamp": timestamp,
            "stubs_registered": len(registered),
            "test_requests_sent": len(test_results),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("WireMock scan error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports")
def list_reports(workspace_path: str, report_base: str = None):
    """List all available report timestamps."""
    report_dir = _report_dir(workspace_path, report_base)
    if not report_dir.exists():
        return {"status": "success", "reports": []}
    reports = sorted(
        [f.stem for f in report_dir.iterdir() if f.is_file()],
        reverse=True,
    )
    return {"status": "success", "reports": reports}


@app.get("/report/{timestamp}")
def get_report(timestamp: str, workspace_path: str, report_base: str = None):
    """Retrieve a scan report by timestamp."""
    report_dir = _report_dir(workspace_path, report_base)
    candidate = report_dir / f"{timestamp}.json"
    if not candidate.exists():
        raise HTTPException(status_code=404, detail=f"No report for timestamp '{timestamp}'")
    with open(candidate) as f:
        data = json.load(f)
    return {"status": "success", "report": data, "report_path": str(candidate)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8130))
    uvicorn.run(app, host="0.0.0.0", port=port)
