"""Subfinder service for subdomain discovery."""

import logging

from clients.enumeration_discovery.subfinder import SubfinderClient
from repositories.workspace import WorkspaceRepository
from services.base_enumeration_discovery import BaseEnumerationDiscoveryService

logger = logging.getLogger(__name__)


class SubfinderService(BaseEnumerationDiscoveryService):
    """Service for Subfinder operations."""

    def __init__(self, repository: WorkspaceRepository, client: SubfinderClient):
        super().__init__(repository, client)
