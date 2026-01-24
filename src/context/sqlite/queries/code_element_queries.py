"""SQL query builders for code element operations."""

from typing import Optional, Tuple, List, Any


def build_insert_query() -> str:
    """Build INSERT query for code element."""
    return """
        INSERT INTO code_elements 
        (element_type, name, qualified_name, file, start_line, end_line, code, language, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """


def build_bulk_insert_query() -> str:
    """Build bulk INSERT query for code elements."""
    return build_insert_query()


def build_get_by_id_query() -> str:
    """Build SELECT query for getting element by ID."""
    return "SELECT * FROM code_elements WHERE id = ?"


def build_get_by_name_query(file: Optional[str] = None) -> Tuple[str, List[Any]]:
    """
    Build SELECT query for getting element by name.
    
    Args:
        file: Optional file path for exact match
        
    Returns:
        Tuple of (query_string, parameters)
    """
    if file:
        return (
            "SELECT * FROM code_elements WHERE name = ? AND file = ? LIMIT 1",
            [file]
        )
    else:
        return (
            "SELECT * FROM code_elements WHERE name = ? LIMIT 1",
            []
        )


def build_get_by_location_query() -> str:
    """Build SELECT query for finding element at specific location."""
    return """
        SELECT * FROM code_elements
        WHERE file = ? AND start_line <= ? AND end_line >= ?
        ORDER BY (end_line - start_line) ASC
        LIMIT 1
    """


def build_search_query(
    name_pattern: Optional[str] = None,
    file_pattern: Optional[str] = None,
    language: Optional[str] = None,
    element_type: Optional[str] = None,
    limit: int = 100
) -> Tuple[str, List[Any]]:
    """
    Build search query with filters.
    
    Args:
        name_pattern: SQL LIKE pattern for name
        file_pattern: SQL LIKE pattern for file
        language: Language filter
        element_type: Element type filter
        limit: Maximum results
        
    Returns:
        Tuple of (query_string, parameters)
    """
    query = "SELECT * FROM code_elements WHERE 1=1"
    params = []
    
    if name_pattern:
        query += " AND name LIKE ?"
        params.append(name_pattern)
    
    if file_pattern:
        query += " AND file LIKE ?"
        params.append(file_pattern)
    
    if language:
        query += " AND language = ?"
        params.append(language)
    
    if element_type:
        query += " AND element_type = ?"
        params.append(element_type)
    
    query += f" LIMIT {limit}"
    
    return (query, params)


def build_clear_query(language: Optional[str] = None) -> Tuple[str, List[Any]]:
    """
    Build DELETE query for clearing elements.
    
    Args:
        language: Optional language filter
        
    Returns:
        Tuple of (query_string, parameters)
    """
    if language:
        return ("DELETE FROM code_elements WHERE language = ?", [language])
    else:
        return ("DELETE FROM code_elements", [])


def build_count_by_language_query() -> str:
    """Build query to count functions by language."""
    return """
        SELECT language, COUNT(*) as count
        FROM code_elements
        WHERE element_type = 'function'
        GROUP BY language
    """


def build_count_functions_query() -> str:
    """Build query to count total functions."""
    return "SELECT COUNT(*) FROM code_elements WHERE element_type = 'function'"
