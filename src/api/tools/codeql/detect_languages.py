"""Detect languages tool."""

from workspace.manager import WorkspaceManager
from tools.codeql_manager import CodeQLManager

workspace_manager = WorkspaceManager()
codeql_manager = CodeQLManager()


def detect_languages(workspace_id: str) -> dict:
    """
    Detect programming languages in a workspace.
    
    Args:
        workspace_id: UUID of the workspace
        
    Returns:
        Dictionary with detected languages list
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
        
        languages = codeql_manager.detect_languages(workspace_path)
        
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
