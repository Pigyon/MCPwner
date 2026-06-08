"""List workspaces tool."""

import logging

from deps import get_workspace_service

logger = logging.getLogger(__name__)


def list_workspaces() -> list:
    """
    List all active workspaces.

    Returns:
        Array of workspace metadata (empty list on error; details are logged)
    """
    try:
        service = get_workspace_service()
        return service.list_workspaces()
    except Exception as e:
        logger.error(f"Failed to list workspaces: {e}")
        return []
