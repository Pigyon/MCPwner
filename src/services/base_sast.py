"""Base service for SAST operations."""

import logging
from typing import List

from clients.base import BaseSASTClient
from repositories.workspace import WorkspaceRepository
from services.base_scan import BaseScanService

logger = logging.getLogger(__name__)


class BaseSASTService(BaseScanService):
    """Base service for SAST operations."""

    SUPPORTED_LANGUAGES: List[str] = []

    def __init__(self, repository: WorkspaceRepository, client: BaseSASTClient):
        super().__init__(repository, client)
        self.tool_category = "sast"

    def is_language_supported(self, language: str) -> bool:
        """
        Check if language is supported.

        Args:
            language: Language name to check

        Returns:
            True if language is supported, False otherwise
        """
        return language.lower() in self.SUPPORTED_LANGUAGES
