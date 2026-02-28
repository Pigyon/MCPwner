"""Get Secrets report tool."""

import logging
from typing import Any, Dict

from deps import get_gitleaks_service, get_trufflehog_service

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = ["gitleaks", "trufflehog"]


def get_secrets_report(tool: str, workspace_id: str) -> Dict[str, Any]:
    """
    Get the latest Secrets report for a workspace.

    Args:
        tool: Name of the Secrets tool
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
    if tool == "gitleaks":
        return get_gitleaks_service()
    if tool == "trufflehog":
        return get_trufflehog_service()
    raise ValueError(f"Unknown tool: {tool}")
