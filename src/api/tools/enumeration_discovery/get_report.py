"""Get Enumeration & Discovery report tool."""

import logging
from typing import Any, Dict

from deps import (
    get_amass_service,
    get_masscan_service,
    get_subfinder_service,
    # get_akto_service,
    # get_arjun_service,
    # get_ffuf_service,
    # get_gau_service,
    # get_gowitness_service,
    # get_httpx_service,
    # get_katana_service,
)

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = [
    "subfinder",
    "amass",
    # "httpx",
    # "katana",
    # "ffuf",
    # "nuclei",
    # "nmap",
    "masscan",
    # "arjun",
    # "gau",
    # "akto",
    # "wafw00f",
    # "gowitness",
]


def get_enumeration_discovery_report(tool: str, workspace_id: str) -> Dict[str, Any]:
    """
    Get the latest Enumeration & Discovery report for a workspace.

    Args:
        tool: Name of the enumeration/discovery tool
        workspace_id: UUID of the workspace

    Returns:
        Report metadata and content
    """
    if tool not in SUPPORTED_TOOLS:
        return {
            "status": "error",
            "error": f"Unsupported tool: {tool}",
            "supported_tools": SUPPORTED_TOOLS,
        }

    try:
        service = _get_service_for_tool(tool)
        return service.get_latest_report(workspace_id)
    except Exception as e:
        logger.error(f"Failed to get report for {tool}: {e}")
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
    # if tool == "nmap":
    #     return get_nmap_service()
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
