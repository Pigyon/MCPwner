"""Main context repository facade."""

from typing import Dict, Any
from ..repositories import ContextRepository, CodeElementRepository, CallGraphRepository
from .repositories.code_element_repository import SQLiteCodeElementRepository
from .repositories.call_graph_repository import SQLiteCallGraphRepository
from .schema import init_context_db
from .connection import get_connection
from .queries import code_element_queries, call_graph_queries


class SQLiteContextRepository(ContextRepository):
    """SQLite implementation of ContextRepository."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._code_elements = SQLiteCodeElementRepository(db_path)
        self._call_graph = SQLiteCallGraphRepository(db_path, self._code_elements)
    
    def initialize(self) -> None:
        """Initialize the repository (create schema)."""
        init_context_db(self.db_path)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count functions by language
            cursor.execute(code_element_queries.build_count_by_language_query())
            functions_by_language = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Count total call relationships
            cursor.execute(call_graph_queries.build_count_relationships_query())
            total_relationships = cursor.fetchone()[0]
            
            # Count total functions
            cursor.execute(code_element_queries.build_count_functions_query())
            total_functions = cursor.fetchone()[0]
            
            return {
                "total_functions": total_functions,
                "functions_by_language": functions_by_language,
                "total_call_relationships": total_relationships
            }
    
    @property
    def code_elements(self) -> CodeElementRepository:
        """Access to code element repository."""
        return self._code_elements
    
    @property
    def call_graph(self) -> CallGraphRepository:
        """Access to call graph repository."""
        return self._call_graph
