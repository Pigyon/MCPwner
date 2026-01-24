"""List functions tool."""

from typing import Optional
from context.search import list_functions as list_func


def list_functions(
    database_id: str,
    language: Optional[str] = None,
    limit: int = 100
) -> dict:
    """
    List all functions in the context database.
    
    This tool retrieves a list of all functions extracted from the codebase.
    Useful for browsing available functions before searching or analyzing.
    
    Args:
        database_id: Database identifier (workspace_id)
        language: Optional language filter (e.g., "python", "javascript", "java")
        limit: Maximum number of results (default: 100, max: 1000)
        
    Returns:
        Dictionary with function list including names, files, and line numbers
        
    Example:
        list_functions(
            database_id="abc-123",
            language="python",
            limit=50
        )
    """
    # Enforce maximum limit
    if limit > 1000:
        limit = 1000
    
    return list_func(
        database_id=database_id,
        language=language,
        limit=limit
    )
