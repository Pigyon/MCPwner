"""List workspaces tool."""

from deps import get_workspace_service


def list_workspaces() -> list:
    """
    List all active workspaces.

    Returns:
        Array of workspace metadata
    """
    service = get_workspace_service()
    return service.list_workspaces()
