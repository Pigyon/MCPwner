"""Get function callees tool."""

from pathlib import Path

from context.sqlite.context_repository import SQLiteContextRepository
from deps import get_workspace_service


def get_callees(workspace_id: str, function_name: str, file: str = None) -> dict:
    """
    Get all functions called by the specified function.

    Args:
        workspace_id: UUID of the workspace
        function_name: Name of the function
        file: Optional file path for exact match

    Returns:
        Dictionary with list of callee functions
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
                "error": "Context database not found. Run extract_code_context first.",
            }

        # Get repository and callees
        repo = SQLiteContextRepository(context_db_path)
        callees = repo.call_graph.get_callees_by_name(function_name, file)

        return {
            "status": "success",
            "function_name": function_name,
            "file": file,
            "callee_count": len(callees),
            "callees": [
                {
                    "name": callee.name,
                    "qualified_name": callee.qualified_name,
                    "file": callee.file,
                    "start_line": callee.start_line,
                    "end_line": callee.end_line,
                    "language": callee.language,
                }
                for callee in callees
            ],
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}
