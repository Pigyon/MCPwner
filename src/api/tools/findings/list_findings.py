"""List findings in the workspace findings ledger."""

from typing import Optional

from api.tools.common import handle_tool_error
from deps import get_findings_service


@handle_tool_error
def list_findings(workspace_id: str, status: Optional[str] = None) -> dict:
    """
    List all findings in the workspace ledger, optionally filtered by status.

    Args:
        workspace_id: UUID of the workspace.
        status: Optional status filter (e.g. "hypothesis", "queued", "poc-confirmed",
            "poc-likely", "poc-fp", "review-approved", "review-disputed",
            "review-rejected"). Omit to return every finding.

    Returns:
        {"status": "success", "workspace_id", "count", "findings": [ ... ]}
    """
    result = get_findings_service().list_findings(workspace_id, status)
    return {"status": "success", **result}
