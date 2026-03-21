"""Masscan service for fast port scanning."""

import logging

from clients.reconnaissance.masscan import MasscanClient
from repositories.workspace import WorkspaceRepository
from services.base_reconnaissance import BaseReconnaissanceService

logger = logging.getLogger(__name__)


class MasscanService(BaseReconnaissanceService):
    """Service for Masscan operations."""

    def __init__(self, repository: WorkspaceRepository, client: MasscanClient):
        super().__init__(repository, client)
