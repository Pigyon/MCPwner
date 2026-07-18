"""CodeQL HTTP client for external service communication."""

import logging
from typing import Any, Dict

import requests

from clients.base import SCAN_TIMEOUT_SECONDS, BaseClient

logger = logging.getLogger(__name__)


class CodeQLClient(BaseClient):
    """HTTP client for CodeQL service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "codeql")

    def create_database(
        self, workspace_id: str, language: str, source_path: str, db_path: str
    ) -> Dict[str, Any]:
        """Create CodeQL database via HTTP."""
        logger.info(f"Creating database for workspace {workspace_id} (language: {language})")
        return self._post_with_background_timeout(
            "/database/create",
            {
                "workspace_id": workspace_id,
                "language": language,
                "source_path": source_path,
                "db_path": db_path,
            },
            SCAN_TIMEOUT_SECONDS,
            (
                f"Database creation exceeded {SCAN_TIMEOUT_SECONDS}s MCP timeout "
                "and is continuing in the background."
            ),
            {"database_path": db_path},
        )

    def execute_query(
        self,
        database_path: str,
        query_pack: str,
        output_path: str,
        query_name: str = None,
        custom_query: str = None,
    ) -> Dict[str, Any]:
        """Execute CodeQL query via HTTP."""
        logger.info(f"Executing query {query_name or query_pack} on {database_path}")
        payload = {
            "database_path": database_path,
            "query_pack": query_pack,
            "output_path": output_path,
        }
        if query_name:
            payload["query_name"] = query_name
        if custom_query:
            payload["custom_query"] = custom_query

        return self._post_with_background_timeout(
            "/query/execute",
            payload,
            SCAN_TIMEOUT_SECONDS,
            (
                f"Query execution exceeded {SCAN_TIMEOUT_SECONDS}s MCP timeout "
                "and is continuing in the background."
            ),
            {"output_path": output_path},
        )

    def list_query_packs(self) -> Dict[str, Any]:
        """List available query packs via HTTP."""
        response = requests.get(f"{self.service_url}/query/packs", timeout=30)
        response.raise_for_status()
        return response.json()
