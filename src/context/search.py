"""Search functionality for code elements in context database."""

from pathlib import Path
from typing import Any, Dict, Optional

from .sqlite.context_repository import SQLiteContextRepository


def search_functions(
    database_id: str,
    pattern: str,
    language: Optional[str] = None,
    file_pattern: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Search for functions matching a pattern.

    Args:
        database_id: Database identifier (workspace_id)
        pattern: Search pattern for function names (supports SQL LIKE wildcards: %, _)
        language: Optional language filter
        file_pattern: Optional file path pattern (supports SQL LIKE wildcards)
        limit: Maximum number of results (default: 100)

    Returns:
        Dictionary with search results and metadata
    """
    context_db_path = f"/workspaces/{database_id}/context.db"

    if not Path(context_db_path).exists():
        return {
            "status": "error",
            "error": f"Context database not found for {database_id}. Run extract_code_context first.",
        }

    try:
        repo = SQLiteContextRepository(context_db_path)

        # Convert simple wildcards to SQL LIKE patterns
        name_pattern = f"%{pattern}%" if "%" not in pattern and "_" not in pattern else pattern

        # Search for functions
        results = repo.code_elements.search(
            name_pattern=name_pattern,
            file_pattern=file_pattern,
            language=language,
            element_type="function",
            limit=limit,
        )

        # Convert to simple dict format
        functions = [
            {
                "name": elem.name,
                "qualified_name": elem.qualified_name,
                "file": elem.file,
                "start_line": elem.start_line,
                "end_line": elem.end_line,
                "language": elem.language,
            }
            for elem in results
        ]

        return {
            "status": "success",
            "database_id": database_id,
            "pattern": pattern,
            "language": language,
            "file_pattern": file_pattern,
            "result_count": len(functions),
            "functions": functions,
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


def list_functions(database_id: str, language: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """
    List all functions in the database.

    Args:
        database_id: Database identifier (workspace_id)
        language: Optional language filter
        limit: Maximum number of results (default: 100)

    Returns:
        Dictionary with function list and metadata
    """
    context_db_path = f"/workspaces/{database_id}/context.db"

    if not Path(context_db_path).exists():
        return {
            "status": "error",
            "error": f"Context database not found for {database_id}. Run extract_code_context first.",
        }

    try:
        repo = SQLiteContextRepository(context_db_path)

        # Search with no pattern to get all functions
        results = repo.code_elements.search(language=language, element_type="function", limit=limit)

        # Convert to simple dict format
        functions = [
            {
                "name": elem.name,
                "qualified_name": elem.qualified_name,
                "file": elem.file,
                "start_line": elem.start_line,
                "end_line": elem.end_line,
                "language": elem.language,
            }
            for elem in results
        ]

        return {
            "status": "success",
            "database_id": database_id,
            "language": language,
            "result_count": len(functions),
            "total_returned": len(functions),
            "limit": limit,
            "functions": functions,
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}
