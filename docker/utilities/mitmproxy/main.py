"""
Mitmproxy Adapter Service

Runs mitmdump as a subprocess proxy, forwards target requests through it,
captures the intercepted traffic, and writes a JSON report.

The LLM uses this to:
  - Intercept HTTP/HTTPS traffic to a live target in real time.
  - Apply on-the-fly request/response modifications via an inline Python addon.
  - Forward manipulated requests and observe how the target reacts.

Config options (passed via ScanRequest.config):
  target:          Required. URL to send through the proxy.
  script:          Optional inline Python mitmproxy addon (as a string).
                   Receives standard mitmproxy hooks: request(flow), response(flow).
  modify_request:  Optional dict of header key/value pairs to inject into every request.
  extra_targets:   Optional list of additional URLs to also send through the proxy.
  timeout:         Seconds to keep the proxy alive (default: 15).
"""

import json
import logging
import os
import signal
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "mitmproxy"
TOOL_CATEGORY = "utilities"

app = FastAPI(title="Mitmproxy Adapter Service", version="1.0.0")

_version_cache: Dict[str, str] = {}


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


def _default_addon(capture_path: str, modify_headers: Dict[str, str]) -> str:
    """Return a mitmdump addon script that captures flows to a JSON file."""
    if modify_headers:
        header_lines = "\n".join(
            f'    flow.request.headers["{k}"] = "{v}"' for k, v in modify_headers.items()
        )
    else:
        header_lines = "    pass"

    return f"""import json

_flows = []

def request(flow):
{header_lines}

def response(flow):
    # get_text(strict=False) avoids charset errors; outer try keeps capture from going empty.
    try:
        try:
            body = flow.response.get_text(strict=False)[:500] if flow.response else ""
        except Exception:
            body = flow.response.content[:500].decode("utf-8", errors="replace") if flow.response else ""
        _flows.append({{
            "method": flow.request.method,
            "url": str(flow.request.pretty_url),
            "request_headers": dict(flow.request.headers),
            "status_code": flow.response.status_code if flow.response else None,
            "response_headers": dict(flow.response.headers) if flow.response else {{}},
            "response_body_snippet": body,
        }})
        with open({repr(capture_path)}, "w") as fh:
            json.dump(_flows, fh)
    except Exception:
        pass
"""


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy", "service": TOOL_NAME}


@app.get("/version", response_model=VersionResponse)
def version():
    if "value" in _version_cache:
        return {"version": _version_cache["value"], "status": "success"}
    try:
        result = subprocess.run(
            ["mitmdump", "--version"], capture_output=True, text=True, timeout=10, check=True
        )
        _version_cache["value"] = result.stdout.strip().split("\n")[0]
        return {"version": _version_cache["value"], "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan")
def scan(request: ScanRequest):
    """
    Start mitmdump, route target request(s) through it, capture intercepted traffic.
    """
    try:
        cfg = request.config or {}
        target: str = cfg.get("target", "")
        if not target:
            raise HTTPException(status_code=400, detail="config.target is required")

        extra_targets: List[str] = cfg.get("extra_targets", [])
        all_targets = [target] + extra_targets
        user_script: Optional[str] = cfg.get("script")
        modify_headers: Dict[str, str] = cfg.get("modify_request", {})
        proxy_timeout: int = int(cfg.get("timeout", 15))

        proxy_port = 8888

        with tempfile.TemporaryDirectory() as tmpdir:
            capture_path = os.path.join(tmpdir, "flows.json")
            addon_path = os.path.join(tmpdir, "addon.py")

            addon_source = user_script if user_script else _default_addon(capture_path, modify_headers)
            with open(addon_path, "w") as f:
                f.write(addon_source)

            proc = subprocess.Popen(
                [
                    "mitmdump",
                    "--listen-port",
                    str(proxy_port),
                    "--ssl-insecure",
                    "--quiet",
                    "-s",
                    addon_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            time.sleep(2)

            proxy_cfg = {
                "http": f"http://localhost:{proxy_port}",
                "https": f"http://localhost:{proxy_port}",
            }

            intercepted = []
            for url in all_targets:
                try:
                    resp = requests.get(url, proxies=proxy_cfg, verify=False, timeout=proxy_timeout)
                    intercepted.append(
                        {
                            "url": url,
                            "status_code": resp.status_code,
                            "body_snippet": resp.text[:500],
                        }
                    )
                except Exception as e:
                    intercepted.append({"url": url, "error": str(e)})

            time.sleep(1)
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

            captured_flows = []
            if os.path.exists(capture_path):
                try:
                    with open(capture_path) as f:
                        captured_flows = json.load(f)
                except Exception:
                    pass

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        output_dir = _report_dir(request.workspace_path, request.report_base)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}.json"

        report = {
            "targets": all_targets,
            "intercepted_requests": intercepted,
            "captured_flows": captured_flows,
            "modify_request_headers": modify_headers,
            "custom_script_used": user_script is not None,
        }
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return {
            "status": "success",
            "finding_count": len(captured_flows),
            "report_path": str(output_path),
            "timestamp": timestamp,
            "flows_captured": len(captured_flows),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Mitmproxy scan error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports")
def list_reports(workspace_path: str, report_base: str = None):
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
    report_dir = _report_dir(workspace_path, report_base)
    candidate = report_dir / f"{timestamp}.json"
    if not candidate.exists():
        raise HTTPException(status_code=404, detail=f"No report for timestamp '{timestamp}'")
    with open(candidate) as f:
        data = json.load(f)
    return {"status": "success", "report": data, "report_path": str(candidate)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8131))
    uvicorn.run(app, host="0.0.0.0", port=port)
