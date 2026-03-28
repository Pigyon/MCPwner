"""Joern service for business logic."""

from config.languages import JOERN_LANGUAGES
from services.base_sast import BaseSASTService


class JoernService(BaseSASTService):
    """Service for Joern SAST operations."""

    SUPPORTED_LANGUAGES = JOERN_LANGUAGES
