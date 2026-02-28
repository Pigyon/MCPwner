import logging

from clients.secrets.detect_secrets import DetectSecretsClient
from repositories.workspace import WorkspaceRepository
from services.base_secrets import BaseSecretsService

logger = logging.getLogger(__name__)


class DetectSecretsService(BaseSecretsService):
    """Service for Detect-Secrets operations."""

    def __init__(self, repository: WorkspaceRepository, client: DetectSecretsClient):
        super().__init__(repository, client)
