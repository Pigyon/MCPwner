"""bbot service for OSINT automation reconnaissance."""

import logging

from clients.reconnaissance.bbot import BbotClient
from repositories.workspace import WorkspaceRepository
from services.base_reconnaissance import BaseReconnaissanceService

logger = logging.getLogger(__name__)


class BbotService(BaseReconnaissanceService):
    """Service for bbot operations."""

    def __init__(self, repository: WorkspaceRepository, client: BbotClient):
        super().__init__(repository, client)
