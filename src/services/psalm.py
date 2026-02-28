"""Psalm service for business logic."""

from config.languages import PSALM_LANGUAGES
from services.base_sast import BaseSASTService


class PsalmService(BaseSASTService):
    """Service for Psalm SAST operations."""

    SUPPORTED_LANGUAGES = PSALM_LANGUAGES
