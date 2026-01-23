"""List workspaces tool."""

from fastmcp import tool
from workspace.manager import WorkspaceManager

workspace_manager = WorkspaceManager()


@tool()
def list_workspaces() -> list:
    """
    List all active workspaces.
    
    Returns:
        Array of workspace metadata
    """
    return workspace_manager.list_workspaces()
