"""Health check tool."""

import logging
import os
from typing import Any, Dict, Optional

from deps import (
    get_bandit_client,
    get_brakeman_client,
    get_codeql_client,
    get_gosec_client,
    get_joern_client,
    get_linguist_client,
    get_nodejsscan_client,
    get_opengrep_client,
    get_pmd_client,
    get_psalm_client,
    get_semgrep_client,
    get_yasa_client,
)

logger = logging.getLogger(__name__)


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
    services = {
        "codeql": get_codeql_client,
        "linguist": get_linguist_client,
        "bandit": get_bandit_client,
        "brakeman": get_brakeman_client,
        "gosec": get_gosec_client,
        "pmd": get_pmd_client,
        "psalm": get_psalm_client,
        "semgrep": get_semgrep_client,
        "nodejsscan": get_nodejsscan_client,
        "joern": get_joern_client,
        "yasa": get_yasa_client,
        "opengrep": get_opengrep_client,
    }

    # Check specific tool
    if tool_name:
        tool_name = tool_name.lower()
        if tool_name not in services:
            return {
                "status": "error",
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(services.keys()),
            }

        client_getter = services[tool_name]
        return _check_service(tool_name, client_getter())

    # Check all services
    results = {
        "status": "healthy",  # Overall status, will change to degraded if any service fails
        "transport": os.environ.get("MCP_TRANSPORT", "stdio"),
        "services": {},
    }

    all_healthy = True
    for name, client_getter in services.items():
        status = _check_service(name, client_getter())
        results["services"][name] = status
        if status["status"] != "healthy":
            all_healthy = False

    if not all_healthy:
        results["status"] = "degraded"

    return results
