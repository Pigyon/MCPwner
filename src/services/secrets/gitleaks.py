import logging
from typing import Any, Dict, Optional

from clients.secrets.gitleaks import GitleaksClient
from repositories.workspace import WorkspaceRepository
from services.base_secrets import BaseSecretsService

logger = logging.getLogger(__name__)


class GitleaksService(BaseSecretsService):
    """Service for Gitleaks operations."""

    def __init__(self, repository: WorkspaceRepository, client: GitleaksClient):
        super().__init__(repository, client)
