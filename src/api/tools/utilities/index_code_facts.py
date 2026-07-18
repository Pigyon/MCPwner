"""Index code structure (functions, classes, methods) for fast triage lookups."""

from deps import get_linguist_service


def index_code_facts(workspace_id: str) -> dict:
    """Build a code-facts index for a workspace (functions, classes, methods with line ranges).

    Use this BEFORE triaging SAST/SCA findings to enable fast context lookups.
    The index is persisted per-workspace and queryable via query_code_facts.

    Args:
        workspace_id: UUID of the workspace to index
    """
    try:
        service = get_linguist_service()
        return service.index_code_facts(workspace_id)
    except Exception as e:
        return {"status": "error", "error": str(e)}
