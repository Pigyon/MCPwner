"""Get Secrets report tool."""

from typing import Any, Dict

from api.tools.common import get_report


def get_secrets_report(tool: str, workspace_id: str) -> Dict[str, Any]:
    """
    Get the latest Secrets report for a workspace.

    Args:
        tool: Name of the Secrets tool
        workspace_id: UUID of the workspace

    Returns:
        Report metadata and content
    """
    return get_report("secrets", tool, workspace_id)
