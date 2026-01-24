"""Detect languages tool."""

from deps import get_codeql_service


def detect_languages(workspace_id: str) -> dict:
    """
    Detect programming languages in a workspace.
    
    Args:
        workspace_id: UUID of the workspace
        
    Returns:
        Dictionary with detected languages list
    """
    try:
        service = get_codeql_service()
        languages = service.detect_languages(workspace_id)
        
        return {
            "workspace_id": workspace_id,
            "languages": languages,
            "count": len(languages)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
