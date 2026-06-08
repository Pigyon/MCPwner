"""Health check tool."""

import logging
import os
from typing import Any, Dict, Optional

from deps import get_client, get_codeql_client, get_linguist_client

logger = logging.getLogger(__name__)

# Tools surfaced by the health check, in display order. CodeQL and Linguist use
# bespoke clients; the rest are resolved generically from the tool registry.
_HEALTH_TOOLS = [
    "codeql",
    "linguist",
    "bandit",
    "brakeman",
    "gosec",
    "pmd",
    "psalm",
    "semgrep",
    "nodejsscan",
    "joern",
    "yasa",
    "opengrep",
]


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
    except Exception as e:
        logger.error(f"Health check failed for {name}: {e}")
        return {
            "status": "unavailable",
            "error": str(e),
        }


def health_check(tool_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Check health of MCPwner services.

    Args:
        tool_name: Optional name of a specific tool to check.
                   If not provided, checks all services.
                   Valid values: codeql, linguist, bandit, brakeman, gosec,
                   pmd, psalm, semgrep, nodejsscan, joern, yasa, opengrep

    Returns:
        Dictionary with health status
    """
    # Check specific tool
    if tool_name:
        tool_name = tool_name.lower()
        if tool_name not in _HEALTH_TOOLS:
            return {
                "status": "error",
                "error": f"Unknown tool: {tool_name}",
                "available_tools": _HEALTH_TOOLS,
            }

        return _check_service(tool_name, _client_for(tool_name))

    # Check all services
    results = {
        "status": "healthy",  # Overall status, will change to degraded if any service fails
        "transport": os.environ.get("MCP_TRANSPORT", "stdio"),
        "services": {},
    }

    all_healthy = True
    for name in _HEALTH_TOOLS:
        status = _check_service(name, _client_for(name))
        results["services"][name] = status
        if status["status"] != "healthy":
            all_healthy = False

    if not all_healthy:
        results["status"] = "degraded"

    return results
