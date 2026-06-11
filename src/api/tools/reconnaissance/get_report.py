"""Get Reconnaissance report tool."""

from typing import Any, Dict

from api.tools.common import get_report


def get_reconnaissance_report(tool: str, workspace_id: str) -> Dict[str, Any]:
    """
    Get the latest Reconnaissance report for a workspace.

    Args:
        tool: Name of the reconnaissance tool
        workspace_id: UUID of the workspace

    Returns:
        Report metadata and content
    """
    return get_report("reconnaissance", tool, workspace_id)
