"""Katana service for web crawling and URL extraction."""

import logging

from clients.reconnaissance.katana import KatanaClient
from repositories.workspace import WorkspaceRepository
from services.base_reconnaissance import BaseReconnaissanceService

logger = logging.getLogger(__name__)


class KatanaService(BaseReconnaissanceService):
    """Service for katana operations."""

    def __init__(self, repository: WorkspaceRepository, client: KatanaClient):
        super().__init__(repository, client)
