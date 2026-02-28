"""Semgrep service for business logic."""

from config.languages import SEMGREP_LANGUAGES
from services.base_sast import BaseSASTService


class SemgrepService(BaseSASTService):
    """Service for Semgrep SAST operations."""

    SUPPORTED_LANGUAGES = SEMGREP_LANGUAGES
