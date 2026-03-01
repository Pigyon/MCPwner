"""Cleanup workspace tool."""

from deps import get_workspace_service


def cleanup_workspace(
    workspace_id: str, delete_files: bool = True, delete_metadata: bool = False
) -> dict:
    """
    Cleanup a workspace with granular control over what gets deleted.

    Args:
        workspace_id: UUID of the workspace to clean up
        delete_files: If True, delete workspace files and scan reports (default: True)
        delete_metadata: If True, also delete workspace metadata from persistence layer.
                        If False, workspace metadata is preserved for future reference (default: False)

    Returns:
        Dictionary with cleanup status and details of what was deleted

    Examples:
        # Delete only files, keep metadata (useful for re-scanning later)
        cleanup_workspace("abc-123", delete_files=True, delete_metadata=False)

        # Complete cleanup including metadata
        cleanup_workspace("abc-123", delete_files=True, delete_metadata=True)

        # Keep files but remove from workspace list (unusual but supported)
        cleanup_workspace("abc-123", delete_files=False, delete_metadata=True)
    """
    try:
        service = get_workspace_service()
        return service.cleanup_workspace(
            workspace_id, delete_files=delete_files, delete_metadata=delete_metadata
        )
    except ValueError as e:
        return {"status": "error", "error": str(e)}
