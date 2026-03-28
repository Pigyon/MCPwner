"""Wafw00f service for Web Application Firewall detection."""

import logging

from clients.reconnaissance.wafw00f import Wafw00fClient
from repositories.workspace import WorkspaceRepository
from services.base_reconnaissance import BaseReconnaissanceService

logger = logging.getLogger(__name__)


class Wafw00fService(BaseReconnaissanceService):
    """Service for wafw00f operations."""

    def __init__(self, repository: WorkspaceRepository, client: Wafw00fClient):
        super().__init__(repository, client)
