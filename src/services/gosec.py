"""Gosec service for business logic."""

from config.languages import GOSEC_LANGUAGES
from services.base_sast import BaseSASTService


class GosecService(BaseSASTService):
    """Service for Gosec SAST operations."""

    SUPPORTED_LANGUAGES = GOSEC_LANGUAGES
