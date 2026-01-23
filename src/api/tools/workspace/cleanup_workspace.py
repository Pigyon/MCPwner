"""Cleanup workspace tool."""

from fastmcp import tool
from workspace.manager import WorkspaceManager

workspace_manager = WorkspaceManager()


@tool()
def cleanup_workspace(workspace_id: str) -> dict:
    """
    Manually cleanup a workspace.
    
    Args:
        workspace_id: UUID of the workspace to clean up
        
    Returns:
        Dictionary with cleanup status
    """
    try:
        return workspace_manager.cleanup_workspace(workspace_id)
    except ValueError as e:
        return {
            "status": "error",
            "error": str(e)
        }
