"""Database connection and operations for context system."""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import contextmanager


@contextmanager
def get_connection(db_path: str):
    """
    Context manager for database connections.
    
    Args:
        db_path: Path to SQLite database file
        
    Yields:
        sqlite3.Connection object
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()


def insert_code_element(
    conn: sqlite3.Connection,
    element_type: str,
    name: str,
    file: str,
    start_line: int,
    end_line: int,
    code: str,
    language: str,
    qualified_name: Optional[str] = None,
    metadata: Optional[str] = None
) -> int:
    """
    Insert a code element into the database.
    
    Args:
        conn: Database connection
        element_type: Type of element ('function', 'method', 'class')
        name: Element name
        file: File path
        start_line: Starting line number
        end_line: Ending line number
        code: Source code
        language: Programming language
        qualified_name: Fully qualified name (optional)
        metadata: JSON metadata string (optional)
        
    Returns:
        ID of inserted element
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO code_elements 
        (element_type, name, qualified_name, file, start_line, end_line, code, language, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (element_type, name, qualified_name, file, start_line, end_line, code, language, metadata)
    )
    conn.commit()
    return cursor.lastrowid


def insert_call_relationship(
    conn: sqlite3.Connection,
    caller_id: int,
    callee_id: int,
    call_site_line: Optional[int] = None
) -> int:
    """
    Insert a call relationship into the call graph.
    
    Args:
        conn: Database connection
        caller_id: ID of calling function
        callee_id: ID of called function
        call_site_line: Line number of call site (optional)
        
    Returns:
        ID of inserted relationship
    """
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO call_graph (caller_id, callee_id, call_site_line) VALUES (?, ?, ?)",
        (caller_id, callee_id, call_site_line)
    )
    conn.commit()
    return cursor.lastrowid


def bulk_insert_code_elements(
    conn: sqlite3.Connection,
    elements: List[Dict[str, Any]]
) -> int:
    """
    Bulk insert code elements for better performance.
    
    Args:
        conn: Database connection
        elements: List of element dictionaries
        
    Returns:
        Number of elements inserted
    """
    cursor = conn.cursor()
    
    # Prepare data tuples
    data = [
        (
            elem.get('element_type'),
            elem.get('name'),
            elem.get('qualified_name'),
            elem.get('file'),
            elem.get('start_line'),
            elem.get('end_line'),
            elem.get('code'),
            elem.get('language'),
            elem.get('metadata')
        )
        for elem in elements
    ]
    
    cursor.executemany(
        """
        INSERT INTO code_elements 
        (element_type, name, qualified_name, file, start_line, end_line, code, language, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        data
    )
    conn.commit()
    return len(elements)


def clear_code_elements(conn: sqlite3.Connection, language: Optional[str] = None) -> int:
    """
    Clear code elements from database.
    
    Args:
        conn: Database connection
        language: Optional language filter (clears all if None)
        
    Returns:
        Number of elements deleted
    """
    cursor = conn.cursor()
    
    if language:
        cursor.execute("DELETE FROM code_elements WHERE language = ?", (language,))
    else:
        cursor.execute("DELETE FROM code_elements")
    
    conn.commit()
    return cursor.rowcount
