"""ffuf service for web fuzzing."""

import logging

from clients.reconnaissance.ffuf import FfufClient
from repositories.workspace import WorkspaceRepository
from services.base_reconnaissance import BaseReconnaissanceService

logger = logging.getLogger(__name__)


class FfufService(BaseReconnaissanceService):
    """Service for ffuf operations."""

    def __init__(self, repository: WorkspaceRepository, client: FfufClient):
        super().__init__(repository, client)
