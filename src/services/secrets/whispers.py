import logging

from clients.secrets.whispers import WhispersClient
from repositories.workspace import WorkspaceRepository
from services.base_secrets import BaseSecretsService

logger = logging.getLogger(__name__)


class WhispersService(BaseSecretsService):
    """Service for Whispers operations."""

    def __init__(self, repository: WorkspaceRepository, client: WhispersClient):
        super().__init__(repository, client)
