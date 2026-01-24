"""Get function context tool."""

from deps import get_workspace_service
from context.sqlite.context_repository import SQLiteContextRepository
from pathlib import Path


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
        workspace_service = get_workspace_service()
        workspace = workspace_service.get_workspace(workspace_id)
        
        # Context database path
        context_db_path = f"/workspaces/{workspace_id}/context.db"
        
        if not Path(context_db_path).exists():
            return {
                "status": "error",
                "error": "Context database not found. Run extract_code_context first."
            }
        
        # Get repository
        repo = SQLiteContextRepository(context_db_path)
        
        # Get function by location or name
        if line is not None and file:
            function = repo.code_elements.get_by_location(file, line)
        elif function_name:
            function = repo.code_elements.get_by_name(function_name, file)
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
                "name": function.name,
                "qualified_name": function.qualified_name,
                "file": function.file,
                "start_line": function.start_line,
                "end_line": function.end_line,
                "code": function.code,
                "language": function.language
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
