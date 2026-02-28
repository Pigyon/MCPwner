"""Bandit service for business logic."""

from config.languages import BANDIT_LANGUAGES
from services.base_sast import BaseSASTService


class BanditService(BaseSASTService):
    """Service for Bandit SAST operations."""

    SUPPORTED_LANGUAGES = BANDIT_LANGUAGES
