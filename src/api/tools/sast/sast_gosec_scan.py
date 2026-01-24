"""Gosec scan MCP tool."""

import sys
from typing import Any, Dict, Optional

from deps import get_gosec_service


def sast_gosec_scan(
    workspace_id: str,
    scan_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Execute Gosec SAST scan on a workspace.

    Args:
        workspace_id: UUID of the workspace to scan
        scan_path: Optional relative path within workspace to scan (defaults to entire workspace)
        config: Optional Gosec configuration (severity, confidence, exclude patterns, etc.)

    Returns:
        Dictionary with scan results including finding count and report path
    """
    print(
        f"[MCP SERVER] sast_gosec_scan called: workspace_id={workspace_id}, scan_path={scan_path}",
        file=sys.stderr,
    )

    try:
        service = get_gosec_service()
        result = service.scan(workspace_id=workspace_id, scan_path=scan_path, config=config)

        if result.get("status") == "success":
            print(
                f"[MCP SERVER] Gosec scan completed: {result.get('finding_count', 0)} findings",
                file=sys.stderr,
            )
        else:
            print(
                f"[MCP SERVER] Gosec scan failed: {result.get('error', 'Unknown error')}",
                file=sys.stderr,
            )

        return result
    except Exception as e:
        error_msg = f"Gosec scan failed: {e}"
        print(f"[MCP SERVER] {error_msg}", file=sys.stderr)
        return {"status": "error", "error": error_msg}
