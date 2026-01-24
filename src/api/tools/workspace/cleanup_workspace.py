"""Cleanup workspace tool."""

from deps import get_workspace_service


def cleanup_workspace(workspace_id: str) -> dict:
    """
    Manually cleanup a workspace.

    Args:
        workspace_id: UUID of the workspace to clean up

    Returns:
        Dictionary with cleanup status
    """
    try:
        service = get_workspace_service()
        return service.cleanup_workspace(workspace_id)
    except ValueError as e:
        return {"status": "error", "error": str(e)}
