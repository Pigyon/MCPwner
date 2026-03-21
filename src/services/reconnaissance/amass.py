"""Amass service for network mapping and attack surface discovery."""

import logging

from clients.reconnaissance.amass import AmassClient
from repositories.workspace import WorkspaceRepository
from services.base_reconnaissance import BaseReconnaissanceService

logger = logging.getLogger(__name__)


class AmassService(BaseReconnaissanceService):
    """Service for Amass operations."""

    def __init__(self, repository: WorkspaceRepository, client: AmassClient):
        super().__init__(repository, client)
