"""Generic SAST report retrieval tool."""

from typing import Any, Dict

from api.tools.common import get_report


def get_sast_report(tool: str, workspace_id: str) -> Dict[str, Any]:
    """
    Get the latest report for a SAST tool.

    Args:
        tool: Name of the SAST tool
        workspace_id: UUID of the workspace

    Returns:
        Report data including SARIF content if available
    """
    return get_report("sast", tool, workspace_id)
