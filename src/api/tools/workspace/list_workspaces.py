"""List workspaces tool."""

from workspace.manager import WorkspaceManager

workspace_manager = WorkspaceManager()


def list_workspaces() -> list:
    """
    List all active workspaces.
    
    Returns:
        Array of workspace metadata
    """
    return workspace_manager.list_workspaces()
