"""Psalm report retrieval MCP tool."""

import sys

from deps import get_psalm_service


def sast_psalm_get_report(workspace_id: str) -> dict:
    """
    Retrieve the most recent Psalm report for a workspace.

    Args:
        workspace_id: UUID of the workspace

    Returns:
        Dictionary with report data including findings and report path
    """
    print(
        f"[MCP SERVER] sast_psalm_get_report called: workspace_id={workspace_id}",
        file=sys.stderr,
    )

    try:
        service = get_psalm_service()
        report = service.get_latest_report(workspace_id)

        if report.get("status") == "success":
            print(
                f"[MCP SERVER] Psalm report retrieved: {report.get('report_path')}",
                file=sys.stderr,
            )
        else:
            print(
                f"[MCP SERVER] Psalm report retrieval failed: {report.get('error', 'Unknown error')}",
                file=sys.stderr,
            )

        return report
    except Exception as e:
        error_msg = f"Failed to retrieve Psalm report: {e}"
        print(f"[MCP SERVER] {error_msg}", file=sys.stderr)
        return {"status": "error", "error": error_msg}
