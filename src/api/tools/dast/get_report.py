"""Generic DAST report retrieval tool."""

from typing import Any, Dict

from api.tools.common import get_report


def get_dast_report(tool: str, workspace_id: str) -> Dict[str, Any]:
    """Get the latest DAST scan report for a tool in a workspace."""
    return get_report("dast", tool, workspace_id)
