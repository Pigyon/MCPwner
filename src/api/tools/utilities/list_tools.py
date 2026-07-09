"""Utilities tool discovery MCP tool."""

from typing import Optional

from api.tools.common import filter_tools_by_language, handle_tool_error

UTILITIES_TOOLS = {
    "linguist": {
        "name": "Linguist",
        "description": (
            "GitHub Linguist language detection. Identifies programming languages "
            "present in a workspace. Use detect_languages instead of run_utilities_scan "
            "for this tool — it has a dedicated MCP tool."
        ),
    },
    "wiremock": {
        "name": "WireMock",
        "description": (
            "API mock server for injecting malicious or unexpected API responses. "
            "When source code reveals third-party API dependencies (payment gateways, "
            "OAuth providers, internal microservices), WireMock stubs those endpoints "
            "with crafted responses (massive payloads, broken JSON, error status codes) "
            "to test whether the target application crashes or has logic bypasses. "
            "Config: target (required, base URL of the live application), stubs (list of "
            "WireMock stub definitions to register), test_requests (list of URLs to "
            "exercise the configured stubs)."
        ),
    },
    "mitmproxy": {
        "name": "Mitmproxy",
        "description": (
            "Man-in-the-middle HTTP/HTTPS proxy for real-time traffic interception and "
            "modification. Intercepts requests from scanners or the target application, "
            "allows the LLM to modify parameters, headers, and body on the fly using "
            "a custom inline Python script, then forwards them to the live instance. "
            "Config: target (required, URL to send through the proxy), script (optional "
            "inline Python addon script for mitmproxy), modify_request (dict of header/param "
            "overrides to apply to intercepted requests)."
        ),
    },
    "fuzzer": {
        "name": "aiohttp Fuzzer",
        "description": (
            "Asynchronous HTTP fuzzer powered by aiohttp. Designed for race condition "
            "testing, multi-threaded parameter fuzzing, and request-smuggling pipelines "
            "where synchronous clients are too slow. Fires batches of concurrent requests "
            "with varied payloads and captures response anomalies. "
            "Config: target (required, base URL), payloads (list of strings to inject), "
            "param (query/body parameter name to fuzz), method (GET/POST/PUT, default GET), "
            "concurrency (max parallel requests, default 50), headers (dict), "
            "timeout (per-request seconds, default 10)."
        ),
    },
    "chromium": {
        "name": "Headless Chromium",
        "description": (
            "Headless Chromium browser via Playwright for client-side vulnerability analysis. "
            "Executes JavaScript-heavy single-page applications to find DOM-based XSS, "
            "front-end authentication bypasses, open redirects, and client-side logic flaws "
            "that raw HTTP clients miss. Captures console output, network requests, DOM "
            "snapshots, and JS errors. "
            "Config: target (required, URL to visit), wait_for (CSS selector or 'networkidle', "
            "default 'networkidle'), check_xss (bool, inject XSS probes into URL params), "
            "screenshot (bool, capture page screenshot), timeout (ms, default 30000)."
        ),
    },
}


@handle_tool_error
def utilities_list_tools(workspace_id: Optional[str] = None, show_all: bool = False) -> dict:
    """
    List available Utilities tools.

    Args:
        workspace_id: Optional workspace ID (reserved for future filtering)
        show_all: If True, show all tools (default behavior for utilities tools)

    Returns:
        Dictionary with available tools and their metadata
    """
    return filter_tools_by_language("utilities", UTILITIES_TOOLS, workspace_id, show_all)
