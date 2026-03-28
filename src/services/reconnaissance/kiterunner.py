"""Kiterunner service for context-aware content discovery."""

import logging

from clients.reconnaissance.kiterunner import KiterunnerClient
from repositories.workspace import WorkspaceRepository
from services.base_reconnaissance import BaseReconnaissanceService

logger = logging.getLogger(__name__)


class KiterunnerService(BaseReconnaissanceService):
    """Service for kiterunner operations."""

    def __init__(self, repository: WorkspaceRepository, client: KiterunnerClient):
        super().__init__(repository, client)
