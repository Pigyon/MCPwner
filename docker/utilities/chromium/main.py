"""
Headless Chromium Service (Playwright)

Drives a headless Chromium browser to analyze JavaScript-heavy single-page
applications and detect client-side vulnerabilities that raw HTTP clients miss.

Two modes:
  1. One-shot (legacy): visit a URL, optionally inject XSS probes.
  2. Scripted actions: run a multi-step Playwright sequence (navigate/click/fill/
     submit/assert) for testing auth flows, IDOR, CSRF, open-redirect oracles.

Config options (passed via ScanRequest.config):
  target:      Required. URL to visit (e.g. "https://example.com").
  wait_for:    CSS selector to wait for, or 'networkidle' (default: 'networkidle').
  check_xss:   Bool — inject XSS probes into URL query parameters (default: false).
  screenshot:  Bool — capture a base64 PNG screenshot (default: false).
  timeout:     Navigation timeout in milliseconds (default: 30000).
  actions:     List[dict] - scripted Playwright steps (see _run_actions). When
               provided, the one-shot analysis is skipped; actions drive the page.
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


async def _run_actions(
    actions: List[Dict[str, Any]],
    target: str,
    timeout_ms: int,
) -> Dict[str, Any]:
    """Execute a scripted Playwright action sequence.

    Supported action types:
      navigate   - {url}
      click      - {selector}
      fill       - {selector, value}
      wait       - {selector} or {ms}
      screenshot - captures at that point
      assert_text     - {selector, contains} oracle: text is present
      assert_url      - {pattern} oracle: current URL matches regex
      assert_visible  - {selector} oracle: element is visible
      assert_hidden   - {selector} oracle: element not visible/absent
      check_xss       - fires the XSS probe oracle on current URL
    """
    results: List[Dict[str, Any]] = []
    oracle_pass: List[Dict[str, Any]] = []
    oracle_fail: List[Dict[str, Any]] = []
    screenshots: List[str] = []
    console_messages: List[Dict[str, str]] = []
    js_errors: List[str] = []

    import re

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        page.on("console", lambda msg: console_messages.append({"type": msg.type, "text": msg.text}))
        page.on("pageerror", lambda err: js_errors.append(str(err)))

        if target:
            try:
                await page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            except Exception as e:
                results.append({"action": "initial_navigate", "status": "error", "error": str(e)})

        for i, step in enumerate(actions):
            action = step.get("action", "")
            step_result: Dict[str, Any] = {"index": i, "action": action}
            try:
                if action == "navigate":
                    await page.goto(step["url"], wait_until="domcontentloaded", timeout=timeout_ms)
                    step_result["status"] = "ok"

                elif action == "click":
                    await page.click(step["selector"], timeout=timeout_ms)
                    step_result["status"] = "ok"

                elif action == "fill":
                    await page.fill(step["selector"], step["value"], timeout=timeout_ms)
                    step_result["status"] = "ok"

                elif action == "wait":
                    if "selector" in step:
                        await page.wait_for_selector(step["selector"], timeout=timeout_ms)
                    elif "ms" in step:
                        await asyncio.sleep(min(int(step["ms"]), 10000) / 1000)
                    step_result["status"] = "ok"

                elif action == "screenshot":
                    shot = await page.screenshot(type="png")
                    screenshots.append(base64.b64encode(shot).decode())
                    step_result["status"] = "ok"

                elif action == "assert_text":
                    el = await page.query_selector(step["selector"])
                    text = (await el.inner_text()) if el else ""
                    expected = step["contains"]
                    if expected in text:
                        oracle_pass.append({"step": i, "type": "assert_text", "detail": expected})
                        step_result["status"] = "pass"
                    else:
                        oracle_fail.append({"step": i, "type": "assert_text", "detail": expected})
                        step_result["status"] = "fail"

                elif action == "assert_url":
                    current = page.url
                    pattern = step["pattern"]
                    if len(pattern) > 1000:
                        oracle_fail.append(
                            {"step": i, "type": "assert_url", "error": "pattern too long"}
                        )
                        step_result["status"] = "fail"
                    elif re.search(pattern, current):
                        oracle_pass.append({"step": i, "type": "assert_url", "url": current})
                        step_result["status"] = "pass"
                    else:
                        oracle_fail.append({"step": i, "type": "assert_url", "url": current})
                        step_result["status"] = "fail"

                elif action == "assert_visible":
                    el = await page.query_selector(step["selector"])
                    visible = (await el.is_visible()) if el else False
                    if visible:
                        oracle_pass.append({"step": i, "type": "assert_visible"})
                        step_result["status"] = "pass"
                    else:
                        oracle_fail.append({"step": i, "type": "assert_visible"})
                        step_result["status"] = "fail"

                elif action == "assert_hidden":
                    el = await page.query_selector(step["selector"])
                    hidden = (not await el.is_visible()) if el else True
                    if hidden:
                        oracle_pass.append({"step": i, "type": "assert_hidden"})
                        step_result["status"] = "pass"
                    else:
                        oracle_fail.append({"step": i, "type": "assert_hidden"})
                        step_result["status"] = "fail"

                elif action == "check_xss":
                    current_url = page.url
                    xss_hit = False
                    for probe in XSS_PROBES:
                        for probe_url in _inject_xss_probe(current_url, probe):
                            try:
                                await page.goto(probe_url, wait_until="domcontentloaded", timeout=10000)
                                await page.wait_for_function("() => window.__xss === 1", timeout=4000)
                                oracle_pass.append({"step": i, "type": "xss", "url": probe_url})
                                xss_hit = True
                                break
                            except Exception:
                                pass
                        if xss_hit:
                            break
                    step_result["status"] = "pass" if xss_hit else "no_trigger"

                else:
                    step_result["status"] = "unknown_action"

            except Exception as e:
                step_result["status"] = "error"
                step_result["error"] = str(e)

            results.append(step_result)

        await browser.close()

    return {
        "steps": results,
        "oracle_pass": oracle_pass,
        "oracle_fail": oracle_fail,
        "oracle_verdict": "pass" if oracle_pass else ("fail" if oracle_fail else "inconclusive"),
        "screenshots": screenshots[:10],
        "console_messages": console_messages,
        "js_errors": js_errors,
    }


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

        try:
            wait_condition = "networkidle" if wait_for == "networkidle" else "domcontentloaded"
            await page.goto(target, wait_until=wait_condition, timeout=timeout_ms)
            if wait_for not in ("networkidle", "domcontentloaded", "load"):
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

        timeout_ms: int = int(cfg.get("timeout", 30000))
        actions: Optional[List[Dict[str, Any]]] = cfg.get("actions")

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        output_dir = _report_dir(request.workspace_path, request.report_base)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}.json"

        if actions:
            logger.info(f"Running {len(actions)} scripted actions against {target}")
            action_data = asyncio.run(_run_actions(actions, target, timeout_ms))

            report = {"target": target, "mode": "actions", **action_data}
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)

            return {
                "status": "success",
                "mode": "actions",
                "finding_count": len(action_data["oracle_pass"]),
                "oracle_verdict": action_data["oracle_verdict"],
                "oracle_pass": action_data["oracle_pass"],
                "oracle_fail": action_data["oracle_fail"],
                "report_path": str(output_path),
                "timestamp": timestamp,
            }

        wait_for: str = cfg.get("wait_for", "networkidle")
        check_xss: bool = bool(cfg.get("check_xss", False))
        take_screenshot: bool = bool(cfg.get("screenshot", False))

        logger.info(f"Analyzing {target} with headless Chromium")

        page_data = asyncio.run(_analyze_page(target, wait_for, check_xss, take_screenshot, timeout_ms))

        finding_count = len(page_data["xss_findings"]) + len(page_data["js_errors"])

        report = {"target": target, "mode": "one-shot", **page_data}
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return {
            "status": "success",
            "mode": "one-shot",
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
