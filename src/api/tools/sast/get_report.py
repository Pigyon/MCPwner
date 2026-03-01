"""Generic SAST report retrieval tool."""

import logging
from typing import Any, Dict

from deps import (
    get_bandit_service,
    get_brakeman_service,
    get_gosec_service,
    get_pmd_service,
    get_psalm_service,
    get_semgrep_service,
)

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = ["semgrep", "bandit", "gosec", "brakeman", "pmd", "psalm"]


def get_sast_report(tool: str, workspace_id: str) -> Dict[str, Any]:
    """
    Get the latest report for a SAST tool.

    Args:
        tool: Name of the SAST tool
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
        return service.get_latest_report(workspace_id)
    except Exception as e:
        logger.error(f"Failed to get report for {tool}: {e}")
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
    raise ValueError(f"Unknown tool: {tool}")
