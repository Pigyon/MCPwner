"""List databases tool."""

from workspace.manager import WorkspaceManager

workspace_manager = WorkspaceManager()


def list_databases(workspace_id: str) -> list:
    """
    List databases for a workspace.
    
    Args:
        workspace_id: UUID of the workspace
        
    Returns:
        Array of database metadata
    """
    try:
        return workspace_manager.list_databases(workspace_id)
    except ValueError as e:
        return [{
            "status": "error",
            "error": str(e)
        }]
