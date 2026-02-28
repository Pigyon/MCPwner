import logging

from clients.secrets.trufflehog import TruffleHogClient
from repositories.workspace import WorkspaceRepository
from services.base_secrets import BaseSecretsService

logger = logging.getLogger(__name__)


class TruffleHogService(BaseSecretsService):
    """Service for TruffleHog operations."""

    def __init__(self, repository: WorkspaceRepository, client: TruffleHogClient):
        super().__init__(repository, client)
