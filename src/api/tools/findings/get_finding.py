"""Get a single finding from the workspace findings ledger."""

from api.tools.common import handle_tool_error
from deps import get_findings_service


@handle_tool_error
def get_finding(workspace_id: str, finding_id: str) -> dict:
    """
    Retrieve a single finding by id from the workspace ledger.

    Args:
        workspace_id: UUID of the workspace.
        finding_id: The finding id (e.g. "F-001").

    Returns:
        The finding object on success, or {"status": "error", "error": ...} if not found.
    """
    finding = get_findings_service().get_finding(workspace_id, finding_id)
    if finding is None:
        return {"status": "error", "error": f"Finding not found: {finding_id}"}
    return finding
