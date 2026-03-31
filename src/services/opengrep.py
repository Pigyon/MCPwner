"""Opengrep service for business logic."""

from config.languages import OPENGREP_LANGUAGES
from services.base_sast import BaseSASTService


class OpengrepService(BaseSASTService):
    """Service for Opengrep SAST operations."""

    SUPPORTED_LANGUAGES = OPENGREP_LANGUAGES
