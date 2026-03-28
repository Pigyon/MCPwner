"""httpx service for HTTP probing and analysis."""

import logging

from clients.reconnaissance.httpx import HttpxClient
from repositories.workspace import WorkspaceRepository
from services.base_reconnaissance import BaseReconnaissanceService

logger = logging.getLogger(__name__)


class HttpxService(BaseReconnaissanceService):
    """Service for httpx operations."""

    def __init__(self, repository: WorkspaceRepository, client: HttpxClient):
        super().__init__(repository, client)
