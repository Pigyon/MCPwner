"""NodeJsScan service for business logic."""

from config.languages import NODEJSSCAN_LANGUAGES
from services.base_sast import BaseSASTService


class NodeJsScanService(BaseSASTService):
    """Service for NodeJsScan SAST operations."""

    SUPPORTED_LANGUAGES = NODEJSSCAN_LANGUAGES
