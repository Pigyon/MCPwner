"""Search functions tool."""

from typing import Optional
from context.search import search_functions as search_func


def search_functions(
    database_id: str,
    pattern: str,
    language: Optional[str] = None,
    file_pattern: Optional[str] = None,
    limit: int = 100
) -> dict:
    """
    Search for functions matching a pattern in the context database.
    
    This tool searches the extracted code context for functions whose names
    match the given pattern. Supports SQL LIKE wildcards (% for any characters,
    _ for single character).
    
    Args:
        database_id: Database identifier (workspace_id)
        pattern: Search pattern for function names (e.g., "get_*", "%handler%", "process_")
        language: Optional language filter (e.g., "python", "javascript")
        file_pattern: Optional file path pattern (e.g., "%/api/%", "%.py")
        limit: Maximum number of results (default: 100, max: 1000)
        
    Returns:
        Dictionary with search results including function names, files, and line numbers
        
    Example:
        search_functions(
            database_id="abc-123",
            pattern="get_%",
            language="python",
            file_pattern="%/api/%"
        )
    """
    # Enforce maximum limit
    if limit > 1000:
        limit = 1000
    
    return search_func(
        database_id=database_id,
        pattern=pattern,
        language=language,
        file_pattern=file_pattern,
        limit=limit
    )
