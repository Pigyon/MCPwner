"""CodeQL service for business logic."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from clients.codeql import CodeQLClient
from config.languages import CODEQL_LANGUAGES
from models import CodeQLDatabase
from repositories.workspace import WorkspaceRepository
from services.linguist import LinguistService

logger = logging.getLogger(__name__)


class CodeQLService:
    """Service for CodeQL operations."""

    def __init__(
        self,
        repository: WorkspaceRepository,
        codeql_client: CodeQLClient,
        linguist_service: LinguistService,
    ):
        self.repository = repository
        self.codeql_client = codeql_client
        self.linguist_service = linguist_service

    def create_database(
        self, workspace_id: str, language: str = None, base_path: str = "/workspaces"
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
            detected_languages = self.linguist_service.detect_languages(workspace_id)
            if not detected_languages:
                raise ValueError("No supported languages detected in workspace")
            language = detected_languages[0]

        # Validate language
        if language not in CODEQL_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        # Check database limit
        existing_dbs = self.repository.find_databases(workspace_id)
        if len(existing_dbs) >= 10:
            raise ValueError(f"Database limit exceeded for workspace {workspace_id}")

        db_path = str(Path(base_path) / workspace_id / "databases" / language)

        # Ensure database parent directory exists
        try:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Log warning but continue, as the directory might be created by the service
            # or volume permissions might prevent it here (though shared volume should allow it)
            logger.warning(f"Failed to create database parent directory: {e}")
            pass

        try:
            result = self.codeql_client.create_database(
                workspace_id=workspace_id,
                language=language,
                source_path=source_path,
                db_path=db_path,
            )

            database = CodeQLDatabase(
                database_id=result.get("database_id", f"{workspace_id}-{language}"),
                workspace_id=workspace_id,
                language=language,
                created_at=datetime.now(timezone.utc),
                path=db_path,
                status="ready",
            )

        except Exception as e:
            logger.error(f"Failed to create CodeQL database: {e}")
            logger.exception("CodeQL database creation error")
            database = CodeQLDatabase(
                database_id=f"{workspace_id}-{language}",
                workspace_id=workspace_id,
                language=language,
                created_at=datetime.now(timezone.utc),
                path=db_path,
                status="failed",
                error=str(e),
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
        output_path: str = None,
    ) -> Dict[str, Any]:
        """Execute CodeQL query."""
        database = self.repository.find_database(workspace_id, database_id)
        if not database:
            raise ValueError(f"Database not found: {database_id}")

        if not output_path:
            output_path = f"/tmp/{workspace_id}_{database_id}_results.sarif"

        resolved_pack = query_pack
        if query_pack in ["security-extended", "security-and-quality", "code-scanning"]:
            # Map generic alias to language-specific suite
            # Example: "security-extended" -> "codeql/python-queries:..."
            resolved_pack = (
                f"codeql/{database.language}-queries:codeql-suites/{database.language}-{query_pack}.qls"
            )
            logger.info(f"Resolved query pack alias '{query_pack}' to '{resolved_pack}'")

        return self.codeql_client.execute_query(
            database_path=database.path, query_pack=resolved_pack, output_path=output_path
        )

    def list_query_packs(self) -> Dict[str, Any]:
        """List available query packs."""
        return self.codeql_client.list_query_packs()

    def get_version(self) -> Dict[str, Any]:
        """Get CodeQL version."""
        return self.codeql_client.get_version()
