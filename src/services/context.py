"""Context extraction service for business logic."""

from typing import Dict, Any, List, Optional
from pathlib import Path
from repositories.workspace import WorkspaceRepository
from context.extraction.extractor_service import ContextExtractorService
from context.sqlite.context_repository import SQLiteContextRepository


class ContextService:
    """Service for code context operations."""
    
    def __init__(
        self,
        repository: WorkspaceRepository,
        codeql_bin: str = "codeql"
    ):
        self.repository = repository
        self.extractor = ContextExtractorService(codeql_bin)
    
    def extract_context(
        self,
        workspace_id: str,
        database_id: str,
        base_path: str = "/workspaces"
    ) -> Dict[str, Any]:
        """Extract code context from CodeQL database."""
        database = self.repository.find_database(workspace_id, database_id)
        if not database:
            raise ValueError(f"Database not found: {database_id}")
        
        context_db_path = str(
            Path(base_path) / workspace_id / "context" / f"{database.language}.db"
        )
        
        # Extract functions
        functions_result = self.extractor.extract_functions(
            database.path,
            context_db_path,
            database.language
        )
        
        if functions_result["status"] != "success":
            return functions_result
        
        # Extract call graph
        callgraph_result = self.extractor.extract_call_graph(
            database.path,
            context_db_path,
            database.language
        )
        
        return {
            "status": "success",
            "functions_extracted": functions_result["functions_extracted"],
            "relationships_extracted": callgraph_result.get("relationships_extracted", 0),
            "duration_seconds": (
                functions_result["duration_seconds"] +
                callgraph_result.get("duration_seconds", 0)
            )
        }
    
    def get_function_context(
        self,
        workspace_id: str,
        language: str,
        function_name: str,
        file: Optional[str] = None,
        base_path: str = "/workspaces"
    ) -> Optional[Dict[str, Any]]:
        """Get function context."""
        context_db_path = str(
            Path(base_path) / workspace_id / "context" / f"{language}.db"
        )
        
        repo = SQLiteContextRepository(context_db_path)
        element = repo.code_elements.get_by_name(function_name, file)
        
        return element.to_dict() if element else None
    
    def get_callers(
        self,
        workspace_id: str,
        language: str,
        function_name: str,
        file: Optional[str] = None,
        base_path: str = "/workspaces"
    ) -> List[Dict[str, Any]]:
        """Get functions that call the specified function."""
        context_db_path = str(
            Path(base_path) / workspace_id / "context" / f"{language}.db"
        )
        
        repo = SQLiteContextRepository(context_db_path)
        callers = repo.call_graph.get_callers_by_name(function_name, file)
        
        return [caller.to_dict() for caller in callers]
    
    def get_callees(
        self,
        workspace_id: str,
        language: str,
        function_name: str,
        file: Optional[str] = None,
        base_path: str = "/workspaces"
    ) -> List[Dict[str, Any]]:
        """Get functions called by the specified function."""
        context_db_path = str(
            Path(base_path) / workspace_id / "context" / f"{language}.db"
        )
        
        repo = SQLiteContextRepository(context_db_path)
        callees = repo.call_graph.get_callees_by_name(function_name, file)
        
        return [callee.to_dict() for callee in callees]
