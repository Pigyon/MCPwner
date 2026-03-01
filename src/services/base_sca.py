"""Base service for SCA operations."""

import logging
from typing import List

from clients.base import BaseSCAClient
from repositories.workspace import WorkspaceRepository
from services.base_static import BaseStaticService

logger = logging.getLogger(__name__)


class BaseSCAService(BaseStaticService):
    """Base service for SCA operations."""

    SUPPORTED_LANGUAGES: List[str] = []

    def __init__(self, repository: WorkspaceRepository, client: BaseSCAClient):
        super().__init__(repository, client)
        self.tool_category = "sca"

    def is_language_supported(self, language: str) -> bool:
        """
        Check if language is supported.

        Args:
            language: Language name to check

        Returns:
            True if language is supported, False otherwise
        """
        # If no supported languages defined, assume it supports everything (e.g. general scanners)
        if not self.SUPPORTED_LANGUAGES:
            return True
        return language.lower() in self.SUPPORTED_LANGUAGES
