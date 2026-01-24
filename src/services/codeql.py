"""CodeQL service for business logic."""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from models import CodeQLDatabase
from repositories.workspace import WorkspaceRepository
from clients.codeql import CodeQLClient


class CodeQLService:
    """Service for CodeQL operations."""
    
    # Supported CodeQL languages with their file extensions
    LANGUAGE_EXTENSIONS = {
        "python": [".py"],
        "javascript": [".js", ".jsx", ".mjs", ".cjs"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "cpp": [".cpp", ".cc", ".cxx", ".c", ".h", ".hpp"],
        "csharp": [".cs"],
        "go": [".go"],
        "ruby": [".rb"],
        "swift": [".swift"],
        "kotlin": [".kt", ".kts"],
        "rust": [".rs"]
    }
    
    def __init__(
        self,
        repository: WorkspaceRepository,
        codeql_client: CodeQLClient
    ):
        self.repository = repository
        self.codeql_client = codeql_client
    
    def detect_languages(self, workspace_id: str) -> List[str]:
        """
        Detect programming languages in a workspace by scanning file extensions.
        
        Args:
            workspace_id: UUID of the workspace
            
        Returns:
            List of detected language names (e.g., ["python", "javascript"])
        """
        workspace = self.repository.find_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        workspace_path = workspace.path or workspace.local_path
        if not workspace_path:
            raise ValueError(f"No source path for workspace: {workspace_id}")
        
        workspace_dir = Path(workspace_path)
        if not workspace_dir.exists():
            return []
        
        detected = set()
        
        # Scan all files in workspace
        for file_path in workspace_dir.rglob("*"):
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                
                # Check against language extensions
                for language, extensions in self.LANGUAGE_EXTENSIONS.items():
                    if suffix in extensions:
                        detected.add(language)
        
        return sorted(list(detected))
    
    def create_database(
        self,
        workspace_id: str,
        language: str = None,
        base_path: str = "/workspaces"
    ) -> Dict[str, Any]:
        """Create CodeQL database for workspace."""
        workspace = self.repository.find_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        source_path = workspace.path or workspace.local_path
        if not source_path:
            raise ValueError(f"No source path for workspace: {workspace_id}")
        
        # Auto-detect language if not provided
        if not language:
            detected_languages = self.detect_languages(workspace_id)
            if not detected_languages:
                raise ValueError("No supported languages detected in workspace")
            language = detected_languages[0]
        
        # Validate language
        if language not in self.LANGUAGE_EXTENSIONS:
            raise ValueError(f"Unsupported language: {language}")
        
        # Check database limit
        existing_dbs = self.repository.find_databases(workspace_id)
        if len(existing_dbs) >= 10:
            raise ValueError(f"Database limit exceeded for workspace {workspace_id}")
        
        db_path = str(Path(base_path) / workspace_id / "databases" / language)
        
        try:
            result = self.codeql_client.create_database(
                workspace_id=workspace_id,
                language=language,
                source_path=source_path,
                db_path=db_path
            )
            
            database = CodeQLDatabase(
                database_id=result.get("database_id", f"{workspace_id}-{language}"),
                workspace_id=workspace_id,
                language=language,
                created_at=datetime.utcnow(),
                path=db_path,
                status="ready"
            )
            
        except Exception as e:
            database = CodeQLDatabase(
                database_id=f"{workspace_id}-{language}",
                workspace_id=workspace_id,
                language=language,
                created_at=datetime.utcnow(),
                path=db_path,
                status="failed",
                error=str(e)
            )
            self.repository.save_database(database)
            raise RuntimeError(f"Database creation failed: {e}")
        
        self.repository.save_database(database)
        return database.model_dump()
    
    def list_databases(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List databases for workspace."""
        databases = self.repository.find_databases(workspace_id)
        return [db.model_dump() for db in databases]
    
    def execute_query(
        self,
        workspace_id: str,
        database_id: str,
        query_pack: str,
        output_path: str = None
    ) -> Dict[str, Any]:
        """Execute CodeQL query."""
        database = self.repository.find_database(workspace_id, database_id)
        if not database:
            raise ValueError(f"Database not found: {database_id}")
        
        if not output_path:
            output_path = f"/tmp/{workspace_id}_{database_id}_results.sarif"
        
        return self.codeql_client.execute_query(
            database_path=database.path,
            query_pack=query_pack,
            output_path=output_path
        )
    
    def list_query_packs(self) -> Dict[str, Any]:
        """List available query packs."""
        return self.codeql_client.list_query_packs()
    
    def get_version(self) -> Dict[str, Any]:
        """Get CodeQL version."""
        return self.codeql_client.get_version()

