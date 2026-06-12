"""Generic IaC report retrieval tool."""

from typing import Any, Dict

from api.tools.common import get_report


def get_iac_report(tool: str, workspace_id: str) -> Dict[str, Any]:
    """
    Get the latest report for an IaC tool.

    Args:
        tool: Name of the IaC tool
        workspace_id: UUID of the workspace

    Returns:
        Report data including SARIF content if available
    """
    return get_report("iac", tool, workspace_id)
