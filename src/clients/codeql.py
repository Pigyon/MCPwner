"""CodeQL HTTP client for external service communication."""

from typing import Any, Dict
import logging

import requests

logger = logging.getLogger(__name__)


class CodeQLClient:
    """HTTP client for CodeQL service."""

    def __init__(self, service_url: str):
        self.service_url = service_url.rstrip("/")

    def create_database(
        self, workspace_id: str, language: str, source_path: str, db_path: str
    ) -> Dict[str, Any]:
        """Create CodeQL database via HTTP."""
        logger.info(f"Creating database for workspace {workspace_id} (language: {language})")
        try:
            response = requests.post(
                f"{self.service_url}/database/create",
                json={
                    "workspace_id": workspace_id,
                    "language": language,
                    "source_path": source_path,
                    "db_path": db_path,
                },
                timeout=600,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create database: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def execute_query(
        self,
        database_path: str,
        query_pack: str,
        output_path: str,
        query_name: str = None,
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

        try:
            response = requests.post(f"{self.service_url}/query/execute", json=payload, timeout=600)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to execute query: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def list_query_packs(self) -> Dict[str, Any]:
        """List available query packs via HTTP."""
        response = requests.get(f"{self.service_url}/query/packs", timeout=30)
        response.raise_for_status()
        return response.json()

    def get_version(self) -> Dict[str, Any]:
        """Get CodeQL version via HTTP."""
        response = requests.get(f"{self.service_url}/version", timeout=10)
        response.raise_for_status()
        return response.json()
