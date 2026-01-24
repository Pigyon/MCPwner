"""Get function callers tool."""

from workspace.manager import WorkspaceManager
from context.sqlite.queries import get_callers as lookup_callers
from pathlib import Path

workspace_manager = WorkspaceManager()


def get_callers(
    workspace_id: str,
    function_name: str,
    file: str = None
) -> dict:
    """
    Get all functions that call the specified function.
    
    Args:
        workspace_id: UUID of the workspace
        function_name: Name of the function
        file: Optional file path for exact match
        
    Returns:
        Dictionary with list of caller functions
    """
    try:
        # Validate workspace
        workspace = workspace_manager.get_workspace(workspace_id)
        if not workspace:
            return {
                "status": "error",
                "error": f"Workspace not found: {workspace_id}"
            }
        
        # Context database path
        context_db_path = f"/workspaces/{workspace_id}/context.db"
        
        if not Path(context_db_path).exists():
            return {
                "status": "error",
                "error": "Context database not found. Run extract_code_context first."
            }
        
        # Get callers
        callers = lookup_callers(context_db_path, function_name, file)
        
        return {
            "status": "success",
            "function_name": function_name,
            "file": file,
            "caller_count": len(callers),
            "callers": [
                {
                    "name": caller["name"],
                    "qualified_name": caller["qualified_name"],
                    "file": caller["file"],
                    "start_line": caller["start_line"],
                    "end_line": caller["end_line"],
                    "language": caller["language"]
                }
                for caller in callers
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
