"""Generic SAST scan tool."""

from typing import Any, Dict, Optional

from api.tools.common import run_scan


def run_sast_scan(
    tool: str,
    workspace_id: str,
    scan_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute a SAST scan using the specified tool.

    Args:
        tool: Name of the SAST tool to run
        workspace_id: UUID of the workspace
        scan_path: Optional relative path within workspace to scan
        config: Optional tool-specific configuration

    Returns:
        Scan results
    """
    return run_scan("sast", tool, workspace_id, scan_path, config)
