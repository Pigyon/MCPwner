"""Arjun service for HTTP parameter discovery."""

import logging

from clients.reconnaissance.arjun import ArjunClient
from repositories.workspace import WorkspaceRepository
from services.base_reconnaissance import BaseReconnaissanceService

logger = logging.getLogger(__name__)


class ArjunService(BaseReconnaissanceService):
    """Service for arjun operations."""

    def __init__(self, repository: WorkspaceRepository, client: ArjunClient):
        super().__init__(repository, client)
