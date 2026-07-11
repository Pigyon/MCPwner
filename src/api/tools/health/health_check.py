"""Health check tool."""

import concurrent.futures
import logging
from typing import Any, Dict, Optional

from config.tools import TOOL_REGISTRY, get_bespoke_tools
from deps import get_client, get_codeql_client, get_linguist_client

logger = logging.getLogger(__name__)


# Registry-driven health checks for all categories, in display order.
def _get_health_tools():
    return get_bespoke_tools() + list(TOOL_REGISTRY.keys())


def _client_for(name: str):
    """Resolve the HTTP client for a health-checked tool."""
    if name == "codeql":
        return get_codeql_client()
    if name == "linguist":
        return get_linguist_client()
    return get_client(name)


def _check_service(name: str, client: Any) -> Dict[str, Any]:
    """
    Check health of a specific service.

    Liveness is decided by the cheap static ``/health`` endpoint. The version
    string (resolved via ``/version``, which executes the tool's CLI and can be
    slow to cold-start) is best-effort: a slow CLI must not make a running
    service report as unavailable.

    Args:
        name: Service name
        client: Service client instance

    Returns:
        Dictionary with service status
    """
    try:
        version_info = client.get_version()
        return {
            "status": "healthy",
            "version": version_info.get("version", "unknown"),
            "details": version_info,
        }
    except Exception as version_error:
        # /version runs the CLI and can transiently time out (cold start) even when
        # the service is up. Fall back to /health to decide liveness.
        try:
            client.get_health()
            logger.warning(f"{name} /version unavailable but /health is OK: {version_error}")
            return {
                "status": "healthy",
                "version": "unknown",
                "note": f"version unavailable: {version_error}",
            }
        except Exception as health_error:
            logger.error(f"Health check failed for {name}: {health_error}")
            return {
                "status": "unavailable",
                "error": str(health_error),
            }


def health_check(tool_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Check health of MCPwner services.

    Args:
        tool_name: Optional name of a specific tool to check.
                   If not provided, checks all wired services (CodeQL, Linguist,
                   and every tool in the registry across all categories — SAST,
                   SCA, Secrets, Reconnaissance, Utilities, IaC).

    Returns:
        Dictionary with health status
    """
    health_tools = _get_health_tools()
    if tool_name:
        tool_name = tool_name.lower()
        if tool_name not in health_tools:
            return {
                "status": "error",
                "error": f"Unknown tool: {tool_name}",
                "available_tools": health_tools,
            }

        return _check_service(tool_name, _client_for(tool_name))

    results = {
        "status": "healthy",  # degraded if any service fails
        "transport": "stdio",
        "services": {},
    }

    all_healthy = True

    def check_tool(name: str):
        return name, _check_service(name, _client_for(name))

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, len(health_tools) or 1)) as executor:
        future_to_name = {executor.submit(check_tool, name): name for name in health_tools}
        for future in concurrent.futures.as_completed(future_to_name):
            name, status = future.result()
            results["services"][name] = status
            if status["status"] != "healthy":
                all_healthy = False

    if not all_healthy:
        results["status"] = "degraded"

    return results
