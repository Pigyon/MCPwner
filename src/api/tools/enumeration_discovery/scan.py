"""Generic Enumeration & Discovery scan tool."""

import logging
from typing import Any, Dict, Optional

from deps import (
    get_amass_service,
    get_masscan_service,
    get_nmap_service,
    get_subfinder_service,
    get_workspace_service,
    # get_akto_service,
    # get_arjun_service,
    # get_ffuf_service,
    # get_gau_service,
    # get_gowitness_service,
    # get_httpx_service,
    # get_katana_service,
    # get_nuclei_service,
    # get_wafw00f_service,
)

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = [
    "subfinder",
    "amass",
    # "httpx",
    # "katana",
    # "ffuf",
    # "nuclei",
    "nmap",
    "masscan",
    # "arjun",
    # "gau",
    # "akto",
    # "wafw00f",
    # "gowitness",
]


def run_enumeration_discovery_scan(
    tool: str,
    workspace_id: Optional[str] = None,
    scan_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute an Enumeration & Discovery scan using the specified tool.

    Args:
        tool: Name of the enumeration/discovery tool to run
        workspace_id: UUID of the workspace (optional - auto-creates virtual workspace if not provided)
        scan_path: Optional relative path within workspace to scan
        config: Optional tool-specific configuration

    Returns:
        Scan results including workspace_id used
    """
    if tool not in SUPPORTED_TOOLS:
        return {
            "status": "error",
            "error": f"Unsupported tool: {tool}",
            "supported_tools": SUPPORTED_TOOLS,
        }

    try:
        # Auto-create virtual workspace if not provided
        if not workspace_id or workspace_id == "auto":
            logger.info("No workspace_id provided, creating virtual workspace for enumeration scan")
            workspace_service = get_workspace_service()
            workspace_result = workspace_service.create_workspace(
                source_type="virtual", source=f"enumeration-{tool}"
            )
            workspace_id = workspace_result["workspace_id"]
            logger.info(f"Created virtual workspace: {workspace_id}")

        service = _get_service_for_tool(tool)
        result = service.scan(workspace_id, scan_path, config)

        # Add workspace_id to result for reference
        if "workspace_id" not in result:
            result["workspace_id"] = workspace_id

        return result
    except Exception as e:
        logger.error(f"Scan failed for {tool}: {e}")
        return {"status": "error", "error": str(e)}


def _get_service_for_tool(tool: str):
    """Get the appropriate service instance for a tool."""
    if tool == "subfinder":
        return get_subfinder_service()
    if tool == "amass":
        return get_amass_service()
    # if tool == "httpx":
    #     return get_httpx_service()
    # if tool == "katana":
    #     return get_katana_service()
    # if tool == "ffuf":
    #     return get_ffuf_service()
    # if tool == "nuclei":
    #     return get_nuclei_service()
    if tool == "nmap":
        return get_nmap_service()
    if tool == "masscan":
        return get_masscan_service()
    # if tool == "arjun":
    #     return get_arjun_service()
    # if tool == "gau":
    #     return get_gau_service()
    # if tool == "akto":
    #     return get_akto_service()
    # if tool == "wafw00f":
    #     return get_wafw00f_service()
    # if tool == "gowitness":
    #     return get_gowitness_service()
    raise ValueError(f"Unknown tool: {tool}")
