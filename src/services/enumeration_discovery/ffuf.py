"""ffuf service for web fuzzing."""

import logging

from clients.enumeration_discovery.ffuf import FfufClient
from repositories.workspace import WorkspaceRepository
from services.base_enumeration_discovery import BaseEnumerationDiscoveryService

logger = logging.getLogger(__name__)


class FfufService(BaseEnumerationDiscoveryService):
    """Service for ffuf operations."""

    def __init__(self, repository: WorkspaceRepository, client: FfufClient):
        super().__init__(repository, client)
