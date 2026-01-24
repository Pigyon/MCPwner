"""List databases tool."""

from deps import get_codeql_service


def list_databases(workspace_id: str) -> list:
    """
    List databases for a workspace.
    
    Args:
        workspace_id: UUID of the workspace
        
    Returns:
        Array of database metadata
    """
    try:
        service = get_codeql_service()
        return service.list_databases(workspace_id)
    except ValueError as e:
        return [{
            "status": "error",
            "error": str(e)
        }]
