"""Brakeman scan MCP tool."""

import sys
from typing import Any, Dict, Optional

from deps import get_brakeman_service


def sast_brakeman_scan(
    workspace_id: str,
    scan_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Execute Brakeman SAST scan on a workspace.

    Args:
        workspace_id: UUID of the workspace to scan
        scan_path: Optional relative path within workspace to scan (defaults to entire workspace)
        config: Optional Brakeman configuration (confidence levels, etc.)

    Returns:
        Dictionary with scan results including finding count and report path
    """
    print(
        f"[MCP SERVER] sast_brakeman_scan called: workspace_id={workspace_id}, scan_path={scan_path}",
        file=sys.stderr,
    )

    try:
        service = get_brakeman_service()
        result = service.scan(workspace_id=workspace_id, scan_path=scan_path, config=config)

        if result.get("status") == "success":
            print(
                f"[MCP SERVER] Brakeman scan completed: {result.get('finding_count', 0)} findings",
                file=sys.stderr,
            )
        else:
            print(
                f"[MCP SERVER] Brakeman scan failed: {result.get('error', 'Unknown error')}",
                file=sys.stderr,
            )

        return result
    except Exception as e:
        error_msg = f"Brakeman scan failed: {e}"
        print(f"[MCP SERVER] {error_msg}", file=sys.stderr)
        return {"status": "error", "error": error_msg}
