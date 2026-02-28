import logging

from clients.secrets.hawk_scanner import HawkScannerClient
from repositories.workspace import WorkspaceRepository
from services.base_secrets import BaseSecretsService

logger = logging.getLogger(__name__)


class HawkScannerService(BaseSecretsService):
    """Service for Hawk-Scanner operations."""

    def __init__(self, repository: WorkspaceRepository, client: HawkScannerClient):
        super().__init__(repository, client)
