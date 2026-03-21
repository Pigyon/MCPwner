"""Masscan service for fast port scanning."""

import logging

from clients.enumeration_discovery.masscan import MasscanClient
from repositories.workspace import WorkspaceRepository
from services.base_enumeration_discovery import BaseEnumerationDiscoveryService

logger = logging.getLogger(__name__)


class MasscanService(BaseEnumerationDiscoveryService):
    """Service for Masscan operations."""

    def __init__(self, repository: WorkspaceRepository, client: MasscanClient):
        super().__init__(repository, client)
