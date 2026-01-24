"""Lookup functions for querying context database."""

import sqlite3
from typing import Dict, Any, List, Optional
from .operations import get_connection


def get_function(
    db_path: str,
    name: str,
    file: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get function by name and optionally file.
    
    Args:
        db_path: Path to context database
        name: Function name
        file: Optional file path for exact match
        
    Returns:
        Function metadata dictionary or None if not found
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        if file:
            # Exact match with file
            cursor.execute(
                """
                SELECT id, element_type, name, qualified_name, file, 
                       start_line, end_line, code, language, metadata
                FROM code_elements
                WHERE element_type = 'function' AND name = ? AND file = ?
                LIMIT 1
                """,
                (name, file)
            )
        else:
            # Fuzzy match without file
            cursor.execute(
                """
                SELECT id, element_type, name, qualified_name, file, 
                       start_line, end_line, code, language, metadata
                FROM code_elements
                WHERE element_type = 'function' AND name = ?
                LIMIT 1
                """,
                (name,)
            )
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_function_by_location(
    db_path: str,
    file: str,
    line: int
) -> Optional[Dict[str, Any]]:
    """
    Find function containing a specific line in a file.
    
    Args:
        db_path: Path to context database
        file: File path
        line: Line number
        
    Returns:
        Function metadata dictionary or None if not found
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, element_type, name, qualified_name, file, 
                   start_line, end_line, code, language, metadata
            FROM code_elements
            WHERE element_type = 'function' 
              AND file = ? 
              AND start_line <= ? 
              AND end_line >= ?
            ORDER BY (end_line - start_line) ASC
            LIMIT 1
            """,
            (file, line, line)
        )
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_callers(
    db_path: str,
    function_name: str,
    file: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get all functions that call the specified function.
    
    Args:
        db_path: Path to context database
        function_name: Name of the function
        file: Optional file path for exact match
        
    Returns:
        List of caller function metadata dictionaries
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # First find the target function
        if file:
            cursor.execute(
                "SELECT id FROM code_elements WHERE name = ? AND file = ? LIMIT 1",
                (function_name, file)
            )
        else:
            cursor.execute(
                "SELECT id FROM code_elements WHERE name = ? LIMIT 1",
                (function_name,)
            )
        
        target_row = cursor.fetchone()
        if not target_row:
            return []
        
        target_id = target_row[0]
        
        # Find all callers
        cursor.execute(
            """
            SELECT DISTINCT ce.id, ce.element_type, ce.name, ce.qualified_name, 
                   ce.file, ce.start_line, ce.end_line, ce.code, ce.language, ce.metadata
            FROM code_elements ce
            JOIN call_graph cg ON ce.id = cg.caller_id
            WHERE cg.callee_id = ?
            """,
            (target_id,)
        )
        
        return [dict(row) for row in cursor.fetchall()]


def get_callees(
    db_path: str,
    function_name: str,
    file: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get all functions called by the specified function.
    
    Args:
        db_path: Path to context database
        function_name: Name of the function
        file: Optional file path for exact match
        
    Returns:
        List of callee function metadata dictionaries
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # First find the source function
        if file:
            cursor.execute(
                "SELECT id FROM code_elements WHERE name = ? AND file = ? LIMIT 1",
                (function_name, file)
            )
        else:
            cursor.execute(
                "SELECT id FROM code_elements WHERE name = ? LIMIT 1",
                (function_name,)
            )
        
        source_row = cursor.fetchone()
        if not source_row:
            return []
        
        source_id = source_row[0]
        
        # Find all callees
        cursor.execute(
            """
            SELECT DISTINCT ce.id, ce.element_type, ce.name, ce.qualified_name, 
                   ce.file, ce.start_line, ce.end_line, ce.code, ce.language, ce.metadata
            FROM code_elements ce
            JOIN call_graph cg ON ce.id = cg.callee_id
            WHERE cg.caller_id = ?
            """,
            (source_id,)
        )
        
        return [dict(row) for row in cursor.fetchall()]


def search_functions(
    db_path: str,
    name_pattern: Optional[str] = None,
    file_pattern: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Search for functions with optional filters.
    
    Args:
        db_path: Path to context database
        name_pattern: SQL LIKE pattern for function name
        file_pattern: SQL LIKE pattern for file path
        language: Programming language filter
        limit: Maximum number of results
        
    Returns:
        List of function metadata dictionaries
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT id, element_type, name, qualified_name, file, 
                   start_line, end_line, code, language, metadata
            FROM code_elements
            WHERE element_type = 'function'
        """
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
        
        query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_database_stats(db_path: str) -> Dict[str, Any]:
    """
    Get statistics about the context database.
    
    Args:
        db_path: Path to context database
        
    Returns:
        Dictionary with database statistics
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Count functions by language
        cursor.execute(
            """
            SELECT language, COUNT(*) as count
            FROM code_elements
            WHERE element_type = 'function'
            GROUP BY language
            """
        )
        functions_by_language = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Count total call relationships
        cursor.execute("SELECT COUNT(*) FROM call_graph")
        total_relationships = cursor.fetchone()[0]
        
        # Count total functions
        cursor.execute("SELECT COUNT(*) FROM code_elements WHERE element_type = 'function'")
        total_functions = cursor.fetchone()[0]
        
        return {
            "total_functions": total_functions,
            "functions_by_language": functions_by_language,
            "total_call_relationships": total_relationships
        }
