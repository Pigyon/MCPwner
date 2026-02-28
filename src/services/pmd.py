"""PMD service for business logic."""

from config.languages import PMD_LANGUAGES
from services.base_sast import BaseSASTService


class PMDService(BaseSASTService):
    """Service for PMD SAST operations."""

    SUPPORTED_LANGUAGES = PMD_LANGUAGES
