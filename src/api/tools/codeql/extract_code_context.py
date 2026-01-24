"""Extract code context tool."""

from workspace.manager import WorkspaceManager
from context.extractor import extract_functions, extract_call_graph
from context.sqlite.queries import get_database_stats
from pathlib import Path

workspace_manager = WorkspaceManager()


def extract_code_context(
    workspace_id: str,
    database_id: str,
    extract_call_graph_flag: bool = True
) -> dict:
    """
    Extract code context from CodeQL database into SQLite context database.
    
    Args:
        workspace_id: UUID of the workspace
        database_id: ID of the CodeQL database (format: workspace_id-language)
        extract_call_graph_flag: Whether to extract call graph (default: True)
        
    Returns:
        Dictionary with extraction results and statistics
    """
    try:
        # Validate workspace
        workspace = workspace_manager.get_workspace(workspace_id)
        if not workspace:
            return {
                "status": "error",
                "error": f"Workspace not found: {workspace_id}"
            }
        
        # Get database metadata
        database = workspace_manager.get_database(workspace_id, database_id)
        if not database:
            return {
                "status": "error",
                "error": f"Database not found: {database_id}"
            }
        
        language = database.get("language")
        db_path = database.get("path")
        
        if not db_path:
            return {
                "status": "error",
                "error": "Database path not found in metadata"
            }
        
        # Context database path
        context_db_path = f"/workspaces/{workspace_id}/context.db"
        
        # Extract functions
        function_result = extract_functions(
            database_path=db_path,
            context_db_path=context_db_path,
            language=language,
            codeql_bin="codeql"
        )
        
        if function_result["status"] != "success":
            return function_result
        
        # Extract call graph if requested
        call_graph_result = None
        if extract_call_graph_flag:
            call_graph_result = extract_call_graph(
                database_path=db_path,
                context_db_path=context_db_path,
                language=language,
                codeql_bin="codeql"
            )
        
        # Get database statistics
        stats = get_database_stats(context_db_path)
        
        return {
            "status": "success",
            "workspace_id": workspace_id,
            "database_id": database_id,
            "context_db_path": context_db_path,
            "functions_extracted": function_result.get("functions_extracted", 0),
            "function_extraction_time": function_result.get("duration_seconds", 0),
            "call_relationships_extracted": call_graph_result.get("relationships_extracted", 0) if call_graph_result else 0,
            "call_graph_extraction_time": call_graph_result.get("duration_seconds", 0) if call_graph_result else 0,
            "statistics": stats
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
