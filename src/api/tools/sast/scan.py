"""Generic SAST scan tool."""

import logging
from typing import Any, Dict, Optional

from deps import (
    get_bandit_service,
    get_brakeman_service,
    get_gosec_service,
    get_joern_service,
    get_nodejsscan_service,
    get_opengrep_service,
    get_pmd_service,
    get_psalm_service,
    get_semgrep_service,
    get_yasa_service,
)

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = [
    "semgrep",
    "bandit",
    "gosec",
    "brakeman",
    "pmd",
    "psalm",
    "nodejsscan",
    "joern",
    "yasa",
    "opengrep",
]


def run_sast_scan(
    tool: str,
    workspace_id: str,
    scan_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute a SAST scan using the specified tool.

    Args:
        tool: Name of the SAST tool to run
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
    if tool == "semgrep":
        return get_semgrep_service()
    if tool == "bandit":
        return get_bandit_service()
    if tool == "gosec":
        return get_gosec_service()
    if tool == "brakeman":
        return get_brakeman_service()
    if tool == "pmd":
        return get_pmd_service()
    if tool == "psalm":
        return get_psalm_service()
    if tool == "nodejsscan":
        return get_nodejsscan_service()
    if tool == "joern":
        return get_joern_service()
    if tool == "yasa":
        return get_yasa_service()
    if tool == "opengrep":
        return get_opengrep_service()
    raise ValueError(f"Unknown tool: {tool}")
