"""YASA service for business logic."""

from config.languages import YASA_LANGUAGES
from services.base_sast import BaseSASTService


class YASAService(BaseSASTService):
    """Service for YASA SAST operations."""

    SUPPORTED_LANGUAGES = YASA_LANGUAGES
