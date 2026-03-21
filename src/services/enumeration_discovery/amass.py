"""Amass service for network mapping and attack surface discovery."""

import logging

from clients.enumeration_discovery.amass import AmassClient
from repositories.workspace import WorkspaceRepository
from services.base_enumeration_discovery import BaseEnumerationDiscoveryService

logger = logging.getLogger(__name__)


class AmassService(BaseEnumerationDiscoveryService):
    """Service for Amass operations."""

    def __init__(self, repository: WorkspaceRepository, client: AmassClient):
        super().__init__(repository, client)
