"""Nmap service for network scanning."""

import logging

from clients.enumeration_discovery.nmap import NmapClient
from repositories.workspace import WorkspaceRepository
from services.base_enumeration_discovery import BaseEnumerationDiscoveryService

logger = logging.getLogger(__name__)


class NmapService(BaseEnumerationDiscoveryService):
    """Service for Nmap operations."""

    def __init__(self, repository: WorkspaceRepository, client: NmapClient):
        super().__init__(repository, client)
