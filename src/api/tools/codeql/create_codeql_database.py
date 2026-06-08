"""Create CodeQL database tool."""

import logging
from typing import Optional

from deps import get_codeql_service

logger = logging.getLogger(__name__)


def create_codeql_database(workspace_id: str, language: Optional[str] = None) -> dict:
    """
    Create CodeQL database for workspace.

    Args:
        workspace_id: UUID of the workspace
        language: Optional language (auto-detect if not provided)

    Returns:
        Dictionary with database_id, language, and status
    """
    try:
        service = get_codeql_service()
        result = service.create_database(workspace_id, language)

        return {
            "database_id": result["database_id"],
            "language": result["language"],
            "status": "success",
            "created_at": result["created_at"],
        }

    except Exception as e:
        logger.error(f"Failed to create CodeQL database: {e}")
        return {"status": "error", "error": str(e)}
