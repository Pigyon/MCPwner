"""Generic Secrets scan tool."""

import logging
from typing import Any, Dict, Optional

from deps import (
    get_detect_secrets_service,
    get_gitleaks_service,
    get_hawk_scanner_service,
    get_trufflehog_service,
    get_whispers_service,
)

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = ["gitleaks", "trufflehog", "whispers", "detect-secrets", "hawk-scanner"]


def run_secrets_scan(
    tool: str,
    workspace_id: str,
    scan_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute a Secrets scan using the specified tool.

    Args:
        tool: Name of the Secrets tool to run
        workspace_id: UUID of the workspace
        scan_path: Optional relative path within workspace to scan
        config: Optional tool-specific configuration

    Returns:
        Scan results
    """
    if tool not in SUPPORTED_TOOLS:
        return {
            "status": "error",
            "error": f"Unsupported tool: {tool}",
            "supported_tools": SUPPORTED_TOOLS,
        }

    try:
        service = _get_service_for_tool(tool)
        return service.scan(workspace_id, scan_path, config)
    except Exception as e:
        logger.error(f"Scan failed for {tool}: {e}")
        return {"status": "error", "error": str(e)}


def _get_service_for_tool(tool: str):
    """Get the appropriate service instance for a tool."""
    if tool == "gitleaks":
        return get_gitleaks_service()
    if tool == "trufflehog":
        return get_trufflehog_service()
    if tool == "whispers":
        return get_whispers_service()
    if tool == "detect-secrets":
        return get_detect_secrets_service()
    if tool == "hawk-scanner":
        return get_hawk_scanner_service()
    raise ValueError(f"Unknown tool: {tool}")
