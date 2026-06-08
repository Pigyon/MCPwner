"""List databases tool."""

import logging

from deps import get_codeql_service

logger = logging.getLogger(__name__)


def list_databases(workspace_id: str) -> list:
    """
    List databases for a workspace.

    Args:
        workspace_id: UUID of the workspace

    Returns:
        Array of database metadata (empty list on error; details are logged)
    """
    try:
        service = get_codeql_service()
        return service.list_databases(workspace_id)
    except Exception as e:
        logger.error(f"Failed to list CodeQL databases: {e}")
        return []
