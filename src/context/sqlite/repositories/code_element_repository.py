"""SQLite implementation of CodeElementRepository."""

from typing import List, Optional

from ...models import CodeElement
from ...repositories import CodeElementRepository
from ..connection import get_connection
from ..queries import code_element_queries as queries


class SQLiteCodeElementRepository(CodeElementRepository):
    """SQLite implementation of CodeElementRepository."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def add(self, element: CodeElement) -> int:
        """Add a code element."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                queries.build_insert_query(),
                (
                    element.element_type,
                    element.name,
                    element.qualified_name,
                    element.file,
                    element.start_line,
                    element.end_line,
                    element.code,
                    element.language,
                    element.metadata,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def bulk_add(self, elements: List[CodeElement]) -> int:
        """Add multiple code elements."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()

            data = [
                (
                    elem.element_type,
                    elem.name,
                    elem.qualified_name,
                    elem.file,
                    elem.start_line,
                    elem.end_line,
                    elem.code,
                    elem.language,
                    elem.metadata,
                )
                for elem in elements
            ]

            cursor.executemany(queries.build_bulk_insert_query(), data)
            conn.commit()
            return len(elements)

    def get_by_id(self, element_id: int) -> Optional[CodeElement]:
        """Get element by ID."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(queries.build_get_by_id_query(), (element_id,))
            row = cursor.fetchone()
            return CodeElement.from_dict(dict(row)) if row else None

    def get_by_name(self, name: str, file: Optional[str] = None) -> Optional[CodeElement]:
        """Get element by name and optional file."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            query, extra_params = queries.build_get_by_name_query(file)
            params = [name] + extra_params
            cursor.execute(query, params)
            row = cursor.fetchone()
            return CodeElement.from_dict(dict(row)) if row else None

    def get_by_location(self, file: str, line: int) -> Optional[CodeElement]:
        """Get element containing a specific line in a file."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(queries.build_get_by_location_query(), (file, line, line))
            row = cursor.fetchone()
            return CodeElement.from_dict(dict(row)) if row else None

    def search(
        self,
        name_pattern: Optional[str] = None,
        file_pattern: Optional[str] = None,
        language: Optional[str] = None,
        element_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[CodeElement]:
        """Search for elements with filters."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            query, params = queries.build_search_query(
                name_pattern, file_pattern, language, element_type, limit
            )
            cursor.execute(query, params)
            return [CodeElement.from_dict(dict(row)) for row in cursor.fetchall()]

    def clear(self, language: Optional[str] = None) -> int:
        """Clear elements, optionally filtered by language."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            query, params = queries.build_clear_query(language)
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
