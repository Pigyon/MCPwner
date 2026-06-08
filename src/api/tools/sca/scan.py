"""Generic SCA scan tool."""

from typing import Any, Dict, Optional

from api.tools.common import run_scan
from config.tools import tools_for_category

SUPPORTED_TOOLS = tools_for_category("sca")


def run_sca_scan(
    tool: str,
    workspace_id: str,
    scan_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute an SCA scan using the specified tool.

    Args:
        tool: Name of the SCA tool to run
        workspace_id: UUID of the workspace
        scan_path: Optional relative path within workspace to scan
        config: Optional tool-specific configuration

    Returns:
        Scan results
    """
    return run_scan("sca", tool, workspace_id, scan_path, config)
