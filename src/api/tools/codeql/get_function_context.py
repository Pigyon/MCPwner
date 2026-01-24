"""Get function context tool."""

from workspace.manager import WorkspaceManager
from context.sqlite.queries import get_function, get_function_by_location
from pathlib import Path

workspace_manager = WorkspaceManager()


def get_function_context(
    workspace_id: str,
    function_name: str = None,
    file: str = None,
    line: int = None
) -> dict:
    """
    Get function context from context database.
    
    Args:
        workspace_id: UUID of the workspace
        function_name: Name of the function (optional if line is provided)
        file: File path (optional for fuzzy matching)
        line: Line number to find containing function (optional)
        
    Returns:
        Dictionary with function metadata including code
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
        
        # Get function by location or name
        if line is not None and file:
            function = get_function_by_location(context_db_path, file, line)
        elif function_name:
            function = get_function(context_db_path, function_name, file)
        else:
            return {
                "status": "error",
                "error": "Either function_name or (file and line) must be provided"
            }
        
        if not function:
            return {
                "status": "not_found",
                "message": "Function not found in context database"
            }
        
        return {
            "status": "success",
            "function": {
                "name": function["name"],
                "qualified_name": function["qualified_name"],
                "file": function["file"],
                "start_line": function["start_line"],
                "end_line": function["end_line"],
                "code": function["code"],
                "language": function["language"]
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
