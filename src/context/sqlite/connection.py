"""Database connection management for context system."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def get_connection(db_path: str):
    """
    Context manager for database connections.
    
    Args:
        db_path: Path to SQLite database file
        
    Yields:
        sqlite3.Connection object with row_factory enabled
    """
    # Ensure parent directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()
