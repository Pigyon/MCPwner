"""
Headless Chromium Service (Playwright)

Drives a headless Chromium browser to analyze JavaScript-heavy single-page
applications and detect client-side vulnerabilities that raw HTTP clients miss.

The LLM uses this to:
  - Execute client-side JavaScript and observe the rendered DOM.
  - Detect DOM-based XSS by injecting probes into URL parameters.
  - Identify open redirects, authentication bypasses, or JS errors.
  - Capture console output and network requests from the live page.
  - Optionally take a screenshot for visual confirmation.

Config options (passed via ScanRequest.config):
  target:      Required. URL to visit (e.g. "https://example.com").
  wait_for:    CSS selector to wait for, or 'networkidle' (default: 'networkidle').
  check_xss:   Bool — inject XSS probes into URL query parameters (default: false).
  screenshot:  Bool — capture a base64 PNG screenshot (default: false).
  timeout:     Navigation timeout in milliseconds (default: 30000).
"""

import asyncio
import base64
import contextlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "chromium"
TOOL_CATEGORY = "utilities"

XSS_PROBES = [
    "<script>window.__xss=1</script>",
    '"><img src=x onerror=window.__xss=1>',
    "javascript:void(window.__xss=1)",
]

# Parameter names to try when the target URL has no query string.
# Covers the most common reflected-input parameters across frameworks.
_COMMON_PARAMS = ["q", "query", "search", "s", "input", "text", "id", "name", "keyword"]

app = FastAPI(title="Headless Chromium Service", version="1.0.0")


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


def _inject_xss_probe(url: str, probe: str) -> List[str]:
    """Return URLs with the probe injected into each existing query parameter.

    When the URL has no query string, try all common parameter names so that
    targets like xss-game.appspot.com/?query= are covered rather than just ?q=.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    if not params:
        return [urlunparse(parsed._replace(query=urlencode({p: probe}))) for p in _COMMON_PARAMS]
    injected = []
    for key in params:
        modified = {k: (probe if k == key else v[0]) for k, v in params.items()}
        new_query = urlencode(modified)
        injected.append(urlunparse(parsed._replace(query=new_query)))
    return injected


async def _analyze_page(
    target: str,
    wait_for: str,
    check_xss: bool,
    take_screenshot: bool,
    timeout_ms: int,
) -> Dict[str, Any]:
    console_messages: List[Dict[str, str]] = []
    network_requests: List[str] = []
    js_errors: List[str] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        page.on("console", lambda msg: console_messages.append({"type": msg.type, "text": msg.text}))
        page.on("pageerror", lambda err: js_errors.append(str(err)))
        page.on("request", lambda req: network_requests.append(req.url))

        # Navigate to target
        try:
            wait_condition = "networkidle" if wait_for == "networkidle" else "domcontentloaded"
            await page.goto(target, wait_until=wait_condition, timeout=timeout_ms)
            if wait_for not in ("networkidle", "domcontentloaded", "load"):
                # Wait for a specific CSS selector
                await page.wait_for_selector(wait_for, timeout=timeout_ms)
        except Exception as e:
            logger.warning(f"Navigation issue: {e}")

        # page.title() throws "Execution context was destroyed" when a SPA triggers
        # a secondary navigation immediately after the initial load.
        try:
            title = await page.title()
        except Exception:
            try:
                title = await page.evaluate("() => document.title")
            except Exception:
                title = ""

        dom_snippet = ""
        with contextlib.suppress(Exception):
            dom_snippet = (await page.content())[:2000]

        # XSS detection
        xss_findings: List[Dict[str, Any]] = []
        if check_xss:
            for probe in XSS_PROBES:
                for probe_url in _inject_xss_probe(target, probe):
                    try:
                        await page.goto(probe_url, wait_until="domcontentloaded", timeout=10000)
                        # wait_for_function polls until the marker is set (handles async
                        # onerror / deferred script execution) rather than a one-shot check.
                        await page.wait_for_function("() => window.__xss === 1", timeout=4000)
                        xss_findings.append({"probe": probe, "url": probe_url, "triggered": True})
                    except Exception:
                        pass

        screenshot_b64: Optional[str] = None
        if take_screenshot:
            try:
                screenshot_bytes = await page.screenshot(type="png")
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
            except Exception as e:
                logger.warning(f"Screenshot failed: {e}")

        await browser.close()

    return {
        "title": title,
        "dom_snippet": dom_snippet,
        "console_messages": console_messages,
        "js_errors": js_errors,
        "network_requests": network_requests[:100],
        "xss_findings": xss_findings,
        "screenshot_png_base64": screenshot_b64,
    }


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy", "service": TOOL_NAME}


@app.get("/version", response_model=VersionResponse)
async def version():
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(args=["--no-sandbox"])
            ver = browser.version
            await browser.close()
        return {"version": ver, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan")
def scan(request: ScanRequest):
    """Navigate to target URL with headless Chromium and analyze for client-side vulnerabilities."""
    try:
        cfg = request.config or {}
        target: str = cfg.get("target", "")
        if not target:
            raise HTTPException(status_code=400, detail="config.target is required")

        wait_for: str = cfg.get("wait_for", "networkidle")
        check_xss: bool = bool(cfg.get("check_xss", False))
        take_screenshot: bool = bool(cfg.get("screenshot", False))
        timeout_ms: int = int(cfg.get("timeout", 30000))

        logger.info(f"Analyzing {target} with headless Chromium")

        page_data = asyncio.run(_analyze_page(target, wait_for, check_xss, take_screenshot, timeout_ms))

        finding_count = len(page_data["xss_findings"]) + len(page_data["js_errors"])

        # Write report
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        output_dir = _report_dir(request.workspace_path, request.report_base)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}.json"

        report = {"target": target, **page_data}
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return {
            "status": "success",
            "finding_count": finding_count,
            "report_path": str(output_path),
            "timestamp": timestamp,
            "title": page_data["title"],
            "xss_findings": len(page_data["xss_findings"]),
            "js_errors": len(page_data["js_errors"]),
            "console_messages": len(page_data["console_messages"]),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chromium scan error")
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

    port = int(os.getenv("PORT", 8133))
    uvicorn.run(app, host="0.0.0.0", port=port)
