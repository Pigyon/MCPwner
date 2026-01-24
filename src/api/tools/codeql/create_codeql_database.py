"""Create CodeQL database tool."""

from deps import get_codeql_service


def create_codeql_database(workspace_id: str, language: str = None) -> dict:
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
            "status": "created",
            "created_at": result["created_at"]
        }
        
    except ValueError as e:
        return {
            "status": "error",
            "error": str(e)
        }
    except RuntimeError as e:
        return {
            "status": "error",
            "error": str(e)
        }
