"""SQLite schema definition for code context database."""

import sqlite3
from pathlib import Path
from typing import Optional


# Schema version for migrations
SCHEMA_VERSION = 1

# SQL schema definition
SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

-- Code elements table (functions, methods, classes)
CREATE TABLE IF NOT EXISTS code_elements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    element_type TEXT NOT NULL,  -- 'function', 'method', 'class', etc.
    name TEXT NOT NULL,
    qualified_name TEXT,  -- Fully qualified name (e.g., 'MyClass.myMethod')
    file TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    code TEXT,  -- Full source code of the element
    language TEXT NOT NULL,
    metadata TEXT  -- JSON string for additional metadata
);

-- Call graph table (caller/callee relationships)
CREATE TABLE IF NOT EXISTS call_graph (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caller_id INTEGER NOT NULL,
    callee_id INTEGER NOT NULL,
    call_site_line INTEGER,
    FOREIGN KEY (caller_id) REFERENCES code_elements(id) ON DELETE CASCADE,
    FOREIGN KEY (callee_id) REFERENCES code_elements(id) ON DELETE CASCADE
);

-- Indexes for code_elements
CREATE INDEX IF NOT EXISTS idx_element_type ON code_elements(element_type);
CREATE INDEX IF NOT EXISTS idx_element_name ON code_elements(name);
CREATE INDEX IF NOT EXISTS idx_element_file ON code_elements(file);
CREATE INDEX IF NOT EXISTS idx_element_language ON code_elements(language);
CREATE INDEX IF NOT EXISTS idx_element_qualified_name ON code_elements(qualified_name);
CREATE INDEX IF NOT EXISTS idx_element_location ON code_elements(file, start_line, end_line);

-- Indexes for call_graph
CREATE INDEX IF NOT EXISTS idx_caller ON call_graph(caller_id);
CREATE INDEX IF NOT EXISTS idx_callee ON call_graph(callee_id);
CREATE INDEX IF NOT EXISTS idx_call_relationship ON call_graph(caller_id, callee_id);
"""


def init_context_db(db_path: str) -> None:
    """
    Initialize context database with schema.
    
    Args:
        db_path: Path to SQLite database file
        
    Raises:
        sqlite3.Error: If database initialization fails
    """
    # Create parent directory if it doesn't exist
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Connect and create schema
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        
        # Execute schema creation
        cursor.executescript(SCHEMA_SQL)
        
        # Insert schema version if not exists
        cursor.execute(
            "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (?, datetime('now'))",
            (SCHEMA_VERSION,)
        )
        
        conn.commit()
    finally:
        conn.close()


def get_schema_version(db_path: str) -> Optional[int]:
    """
    Get current schema version from database.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        Schema version number or None if not found
    """
    if not Path(db_path).exists():
        return None
    
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error:
        return None
    finally:
        conn.close()
