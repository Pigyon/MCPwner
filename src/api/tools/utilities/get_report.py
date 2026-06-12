"""Get Utilities report tool."""

from typing import Any, Dict

from api.tools.common import get_report


def get_utilities_report(tool: str, workspace_id: str) -> Dict[str, Any]:
    """
    Get the latest Utilities report for a workspace.

    Args:
        tool: Name of the utilities tool (wiremock, mitmproxy, fuzzer, chromium)
        workspace_id: UUID of the workspace

    Returns:
        Report metadata and content
    """
    return get_report("utilities", tool, workspace_id)
