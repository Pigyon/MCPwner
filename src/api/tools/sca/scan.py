"""Generic SCA scan tool."""

import logging
from typing import Any, Dict, Optional

from deps import get_osv_scanner_service, get_grype_service, get_syft_service, get_retirejs_service

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = ["osv-scanner", "grype", "retirejs", "syft"]


def run_sca_scan(
    tool: str,
    workspace_id: str,
    scan_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute an SCA scan using the specified tool.

    Args:
        tool: Name of the SCA tool to run
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
        if not service:
             return {
                "status": "error",
                "error": f"Service for tool '{tool}' is not implemented yet.",
            }
        return service.scan(workspace_id, scan_path, config)
    except Exception as e:
        logger.error(f"Scan failed for {tool}: {e}")
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
