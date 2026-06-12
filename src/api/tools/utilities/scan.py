"""Run Utilities scan tool."""

import logging
from typing import Any, Dict, Optional

from config.tools import resolve_tool_name, tools_for_category
from deps import get_service, get_workspace_service

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = tools_for_category("utilities")

AUTO_WORKSPACE = "auto"


def run_utilities_scan(
    tool: str,
    target: Optional[str] = None,
    workspace_id: Optional[str] = None,
    scan_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute a Utilities scan using the specified tool.

    Args:
        tool: Name of the utilities tool to run.
              Supported: wiremock, mitmproxy, fuzzer, chromium.
        target: The URL or endpoint to analyze (e.g. "https://example.com").
                Required for all tools. Can also be passed via config['target'].
        workspace_id: UUID of the workspace (optional - auto-creates if not provided).
                      Reuse the same workspace_id across chained scans to keep
                      all reports together.
        scan_path: Not used for URL-based utilities scans (ignored).
        config: Optional tool-specific configuration dict.

            WIREMOCK config:
              stubs: list of WireMock stub definition dicts to register
                     Each stub follows WireMock's mappings format:
                     {"request": {"method": "GET", "url": "/api/pay"},
                      "response": {"status": 500, "body": "crash"}}
              test_requests: list of paths to GET after stubs are registered

            MITMPROXY config:
              script: optional inline Python addon for mitmproxy
                      (receives request/response objects for modification)
              modify_request: dict of header overrides to apply to every request
                              e.g. {"X-Forwarded-For": "127.0.0.1"}

            FUZZER config:
              payloads: list of strings to inject as parameter values
              param: query/body parameter name to fuzz (default: 'q')
              method: HTTP method (GET/POST/PUT, default: GET)
              concurrency: max parallel requests (default: 50)
              headers: dict of extra headers
              timeout: per-request timeout in seconds (default: 10)

            CHROMIUM config:
              wait_for: CSS selector or 'networkidle' to wait for before capture
                        (default: 'networkidle')
              check_xss: bool — inject XSS probes into URL parameters (default: false)
              screenshot: bool — capture a page screenshot (default: false)
              timeout: navigation timeout in milliseconds (default: 30000)

    Returns:
        Scan results with workspace_id, finding_count, and tool-specific summary.
    """
    if target:
        config = {**(config or {}), "target": target}
    elif not (config and config.get("target")):
        return {
            "status": "error",
            "error": (
                "A 'target' is required (e.g. target='https://example.com'). "
                f"Supported tools: {', '.join(SUPPORTED_TOOLS)}."
            ),
        }

    tool = resolve_tool_name(tool)
    if tool not in SUPPORTED_TOOLS:
        return {
            "status": "error",
            "error": f"Unsupported tool: {tool}",
            "supported_tools": SUPPORTED_TOOLS,
        }

    try:
        if not workspace_id or workspace_id == AUTO_WORKSPACE:
            logger.info("No workspace_id provided, creating virtual workspace for utilities scan")

            workspace_service = get_workspace_service()
            workspace_result = workspace_service.create_workspace(
                source_type="virtual", source=f"utilities-{tool}"
            )
            workspace_id = workspace_result["workspace_id"]

            logger.info(f"Created virtual workspace: {workspace_id}")

        service = get_service(tool)
        result = service.scan(workspace_id, scan_path, config)

        if "workspace_id" not in result:
            result["workspace_id"] = workspace_id

        return result

    except Exception as e:
        logger.error(f"Utilities scan failed for {tool}: {e}")
        return {"status": "error", "error": str(e)}
