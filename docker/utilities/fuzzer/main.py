"""
aiohttp Fuzzer Service

Fires highly concurrent HTTP requests against a target using aiohttp, designed
for race condition testing, parameter fuzzing, and request-smuggling pipelines
where synchronous clients are too slow.

The LLM uses this to:
  - Test race conditions by firing many simultaneous requests.
  - Fuzz a parameter with a list of malicious payloads.
  - Identify anomalous responses by status code, size, or timing deviation.

Config options (passed via ScanRequest.config):
  target:      Required. Base URL to fuzz (e.g. "https://example.com/api/login").
  payloads:    List of strings to inject as the fuzz parameter value.
               Defaults to a small built-in set of common injection probes.
  param:       Query/body parameter name to fuzz (default: 'q').
  method:      HTTP method — GET, POST, PUT (default: GET).
  concurrency: Max parallel requests (default: 50).
  headers:     Dict of extra HTTP headers to include in every request.
  timeout:     Per-request timeout in seconds (default: 10).
"""

import asyncio
import json
import logging
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "fuzzer"
TOOL_CATEGORY = "utilities"

app = FastAPI(title="aiohttp Fuzzer Service", version="1.0.0")

DEFAULT_PAYLOADS = [
    "' OR '1'='1",
    "<script>alert(1)</script>",
    "../../../etc/passwd",
    "{{7*7}}",
    "${7*7}",
    "admin",
    "' UNION SELECT NULL--",
    "%00",
    "A" * 8192,
    "\x00\x0a\x0d",
]


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


async def _fuzz_single(
    session: aiohttp.ClientSession,
    url: str,
    method: str,
    param: str,
    payload: str,
    extra_headers: Dict[str, str],
    timeout: float,
) -> Dict[str, Any]:
    start = time.monotonic()
    try:
        kwargs: Dict[str, Any] = {
            "headers": extra_headers,
            "timeout": aiohttp.ClientTimeout(total=timeout),
        }
        if method == "GET":
            kwargs["params"] = {param: payload}
            async with session.get(url, **kwargs) as resp:
                body = await resp.text()
                elapsed = time.monotonic() - start
                return {
                    "payload": payload,
                    "status_code": resp.status,
                    "content_length": len(body),
                    "elapsed_ms": round(elapsed * 1000, 1),
                    "body_snippet": body[:300],
                }
        else:
            data = {param: payload}
            async with getattr(session, method.lower())(url, data=data, **kwargs) as resp:
                body = await resp.text()
                elapsed = time.monotonic() - start
                return {
                    "payload": payload,
                    "status_code": resp.status,
                    "content_length": len(body),
                    "elapsed_ms": round(elapsed * 1000, 1),
                    "body_snippet": body[:300],
                }
    except asyncio.TimeoutError:
        return {
            "payload": payload,
            "error": "timeout",
            "elapsed_ms": round((time.monotonic() - start) * 1000, 1),
        }
    except Exception as e:
        return {
            "payload": payload,
            "error": str(e),
            "elapsed_ms": round((time.monotonic() - start) * 1000, 1),
        }


async def _run_fuzzer(
    url: str,
    payloads: List[str],
    param: str,
    method: str,
    concurrency: int,
    extra_headers: Dict[str, str],
    timeout: float,
) -> List[Dict[str, Any]]:
    semaphore = asyncio.Semaphore(concurrency)
    connector = aiohttp.TCPConnector(ssl=False)

    async def bounded(payload: str) -> Dict[str, Any]:
        async with semaphore:
            return await _fuzz_single(session, url, method, param, payload, extra_headers, timeout)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [bounded(p) for p in payloads]
        return await asyncio.gather(*tasks)


def _detect_anomalies(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flag results that deviate from the baseline (most common status + median size)."""
    successful = [r for r in results if "status_code" in r]
    if not successful:
        return []

    status_counts: Dict[int, int] = {}
    for r in successful:
        status_counts[r["status_code"]] = status_counts.get(r["status_code"], 0) + 1
    baseline_status = max(status_counts, key=status_counts.__getitem__)

    sizes = [r["content_length"] for r in successful]
    median_size = statistics.median(sizes) if sizes else 0
    size_threshold = max(200, median_size * 0.3)

    anomalies = []
    for r in successful:
        reasons = []
        if r["status_code"] != baseline_status:
            reasons.append(f"unexpected status {r['status_code']} (baseline: {baseline_status})")
        if abs(r["content_length"] - median_size) > size_threshold:
            reasons.append(f"unusual content length {r['content_length']} (median: {median_size})")
        if reasons:
            anomalies.append({**r, "anomaly_reasons": reasons})

    return anomalies


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy", "service": TOOL_NAME}


@app.get("/version", response_model=VersionResponse)
def version():
    return {"version": aiohttp.__version__, "status": "success"}


@app.post("/scan")
def scan(request: ScanRequest):
    """Fire concurrent HTTP requests with varied payloads, detect anomalous responses."""
    try:
        cfg = request.config or {}
        target: str = cfg.get("target", "")
        if not target:
            raise HTTPException(status_code=400, detail="config.target is required")

        payloads: List[str] = cfg.get("payloads", DEFAULT_PAYLOADS)
        param: str = cfg.get("param", "q")
        method: str = cfg.get("method", "GET").upper()
        concurrency: int = int(cfg.get("concurrency", 50))
        extra_headers: Dict[str, str] = cfg.get("headers", {})
        timeout: float = float(cfg.get("timeout", 10))

        if method not in ("GET", "POST", "PUT"):
            raise HTTPException(
                status_code=400, detail=f"Unsupported method: {method}. Use GET, POST, or PUT."
            )

        logger.info(f"Fuzzing {target} with {len(payloads)} payloads (concurrency={concurrency})")

        results = asyncio.run(
            _run_fuzzer(target, payloads, param, method, concurrency, extra_headers, timeout)
        )

        anomalies = _detect_anomalies(results)

        # Write report
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        output_dir = _report_dir(request.workspace_path, request.report_base)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}.json"

        report = {
            "target": target,
            "param": param,
            "method": method,
            "payloads_sent": len(payloads),
            "anomalies_found": len(anomalies),
            "anomalies": anomalies,
            "all_results": results,
        }
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return {
            "status": "success",
            "finding_count": len(anomalies),
            "report_path": str(output_path),
            "timestamp": timestamp,
            "payloads_sent": len(payloads),
            "anomalies_found": len(anomalies),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Fuzzer scan error")
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

    port = int(os.getenv("PORT", 8132))
    uvicorn.run(app, host="0.0.0.0", port=port)
