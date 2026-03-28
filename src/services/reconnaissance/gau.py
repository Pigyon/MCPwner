"""gau service for fetching URLs from web archives."""

import logging

from clients.reconnaissance.gau import GauClient
from repositories.workspace import WorkspaceRepository
from services.base_reconnaissance import BaseReconnaissanceService

logger = logging.getLogger(__name__)


class GauService(BaseReconnaissanceService):
    """Service for gau operations."""

    def __init__(self, repository: WorkspaceRepository, client: GauClient):
        super().__init__(repository, client)
