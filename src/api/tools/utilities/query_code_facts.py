"""Query the persisted code-facts index for triage context."""

from typing import Optional

from deps import get_linguist_service


def query_code_facts(
    workspace_id: str,
    file: Optional[str] = None,
    kind: Optional[str] = None,
    name: Optional[str] = None,
) -> dict:
    """Query the code-facts index for symbols matching the given filters.

    Use this to quickly look up callers, type definitions, or scope for a finding
    during triage — avoids expensive per-finding CodeQL/Joern queries.

    Args:
        workspace_id: UUID of the workspace (must have been indexed first)
        file: Filter by file path (substring match)
        kind: Filter by symbol kind (function, class, method, struct, etc.)
        name: Filter by symbol name (case-insensitive substring)
    """
    try:
        service = get_linguist_service()
        return service.query_code_facts(workspace_id, file=file, kind=kind, name=name)
    except Exception as e:
        return {"status": "error", "error": str(e)}
