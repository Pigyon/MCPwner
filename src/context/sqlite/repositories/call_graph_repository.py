"""SQLite implementation of CallGraphRepository."""

from typing import List, Optional

from ...models import CallRelationship, CodeElement
from ...repositories import CallGraphRepository
from ..connection import get_connection
from ..queries import call_graph_queries as queries


class SQLiteCallGraphRepository(CallGraphRepository):
    """SQLite implementation of CallGraphRepository."""

    def __init__(self, db_path: str, code_element_repo):
        self.db_path = db_path
        self.code_element_repo = code_element_repo

    def add(self, relationship: CallRelationship) -> int:
        """Add a call relationship."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                queries.build_insert_relationship_query(),
                (
                    relationship.caller_id,
                    relationship.callee_id,
                    relationship.call_site_line,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_callers(self, element_id: int) -> List[CodeElement]:
        """Get all elements that call the specified element."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(queries.build_get_callers_query(), (element_id,))
            return [CodeElement.from_dict(dict(row)) for row in cursor.fetchall()]

    def get_callees(self, element_id: int) -> List[CodeElement]:
        """Get all elements called by the specified element."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(queries.build_get_callees_query(), (element_id,))
            return [CodeElement.from_dict(dict(row)) for row in cursor.fetchall()]

    def get_callers_by_name(self, function_name: str, file: Optional[str] = None) -> List[CodeElement]:
        """Get callers by function name."""
        target = self.code_element_repo.get_by_name(function_name, file)
        if not target:
            return []
        return self.get_callers(target.id)

    def get_callees_by_name(self, function_name: str, file: Optional[str] = None) -> List[CodeElement]:
        """Get callees by function name."""
        source = self.code_element_repo.get_by_name(function_name, file)
        if not source:
            return []
        return self.get_callees(source.id)
