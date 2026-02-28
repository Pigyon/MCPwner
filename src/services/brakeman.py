"""Brakeman service for business logic."""

from config.languages import BRAKEMAN_LANGUAGES
from services.base_sast import BaseSASTService


class BrakemanService(BaseSASTService):
    """Service for Brakeman SAST operations."""

    SUPPORTED_LANGUAGES = BRAKEMAN_LANGUAGES
