"""Nmap service for network scanning."""

import logging

from clients.reconnaissance.nmap import NmapClient
from repositories.workspace import WorkspaceRepository
from services.base_reconnaissance import BaseReconnaissanceService

logger = logging.getLogger(__name__)


class NmapService(BaseReconnaissanceService):
    """Service for Nmap operations."""

    def __init__(self, repository: WorkspaceRepository, client: NmapClient):
        super().__init__(repository, client)
