"""Create CodeQL database tool."""

from workspace.manager import WorkspaceManager
from tools.codeql_manager import CodeQLManager

workspace_manager = WorkspaceManager()
codeql_manager = CodeQLManager()


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
        workspace = workspace_manager.get_workspace(workspace_id)
        if not workspace:
            return {
                "status": "error",
                "error": f"Workspace not found: {workspace_id}"
            }
        
        workspace_path = workspace.get("path")
        if not workspace_path:
            return {
                "status": "error",
                "error": "Workspace path not found"
            }
        
        if not language:
            detected_languages = codeql_manager.detect_languages(workspace_path)
            if not detected_languages:
                return {
                    "status": "error",
                    "error": "No supported languages detected in workspace"
                }
            language = detected_languages[0]
        
        db_metadata = codeql_manager.create_database(
            workspace_id=workspace_id,
            language=language,
            workspace_path=workspace_path
        )
        
        workspace_manager.add_database(workspace_id, db_metadata)
        
        return {
            "database_id": db_metadata["database_id"],
            "language": db_metadata["language"],
            "status": "created",
            "created_at": db_metadata["created_at"]
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
