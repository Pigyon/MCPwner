"""Brakeman report retrieval MCP tool."""

import sys

from deps import get_brakeman_service


def sast_brakeman_get_report(workspace_id: str) -> dict:
    """
    Retrieve the most recent Brakeman report for a workspace.

    Args:
        workspace_id: UUID of the workspace

    Returns:
        Dictionary with report metadata and SARIF content
    """
    print(
        f"[MCP SERVER] sast_brakeman_get_report called: workspace_id={workspace_id}",
        file=sys.stderr,
    )

    try:
        service = get_brakeman_service()
        report = service.get_latest_report(workspace_id)

        if report.get("status") == "success":
            print(
                f"[MCP SERVER] Brakeman report retrieved: {report.get('report_path')}",
                file=sys.stderr,
            )
        else:
            print(
                f"[MCP SERVER] Failed to retrieve report: {report.get('error', 'Unknown error')}",
                file=sys.stderr,
            )

        return report
    except Exception as e:
        error_msg = f"Failed to retrieve Brakeman report: {e}"
        print(f"[MCP SERVER] {error_msg}", file=sys.stderr)
        return {"status": "error", "error": error_msg}
