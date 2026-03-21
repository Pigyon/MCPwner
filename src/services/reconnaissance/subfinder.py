"""Subfinder service for subdomain discovery."""

import logging

from clients.reconnaissance.subfinder import SubfinderClient
from repositories.workspace import WorkspaceRepository
from services.base_reconnaissance import BaseReconnaissanceService

logger = logging.getLogger(__name__)


class SubfinderService(BaseReconnaissanceService):
    """Service for Subfinder operations."""

    def __init__(self, repository: WorkspaceRepository, client: SubfinderClient):
        super().__init__(repository, client)
