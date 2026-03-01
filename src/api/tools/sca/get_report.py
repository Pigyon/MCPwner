"""Generic SCA report retrieval tool."""

import logging
from typing import Any, Dict

from deps import get_osv_scanner_service, get_grype_service, get_syft_service, get_retirejs_service

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = ["osv-scanner", "grype", "retirejs", "syft"]


def get_sca_report(tool: str, workspace_id: str) -> Dict[str, Any]:
    """
    Get the latest report for an SCA tool.

    Args:
        tool: Name of the SCA tool
        workspace_id: UUID of the workspace

    Returns:
        Report data including SARIF content if available
    """
    if tool not in SUPPORTED_TOOLS:
        return {
            "status": "error",
            "error": f"Unsupported tool: {tool}",
            "supported_tools": SUPPORTED_TOOLS,
        }

    try:
        service = _get_service_for_tool(tool)
        if not service:
            return {
                "status": "error",
                "error": f"Service for tool '{tool}' is not implemented yet.",
            }
        return service.get_latest_report(workspace_id)
    except Exception as e:
        logger.error(f"Failed to get report for {tool}: {e}")
        return {"status": "error", "error": str(e)}


def _get_service_for_tool(tool: str):
    """Get the appropriate service instance for a tool."""
    if tool == "osv-scanner":
        return get_osv_scanner_service()
    elif tool == "grype":
        return get_grype_service()
    elif tool == "retirejs":
        return get_retirejs_service()
    elif tool == "syft":
        return get_syft_service()
    else:
        raise ValueError(f"Unknown tool: {tool}")
