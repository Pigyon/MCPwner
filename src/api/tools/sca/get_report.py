"""Generic SCA report retrieval tool."""

from typing import Any, Dict

from api.tools.common import get_report


def get_sca_report(tool: str, workspace_id: str) -> Dict[str, Any]:
    """
    Get the latest report for an SCA tool.

    Args:
        tool: Name of the SCA tool
        workspace_id: UUID of the workspace

    Returns:
        Report data including SARIF content if available
    """
    return get_report("sca", tool, workspace_id)
