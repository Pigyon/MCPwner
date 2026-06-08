"""Base service for Reconnaissance operations."""

from clients.base_reconnaissance import BaseReconnaissanceClient
from config.tools import ToolCategory
from repositories.workspace import WorkspaceRepository
from services.base_scan import BaseScanService


class BaseReconnaissanceService(BaseScanService):
    """Base service for Reconnaissance operations."""

    def __init__(self, repository: WorkspaceRepository, client: BaseReconnaissanceClient):
        super().__init__(repository, client)
        self.tool_category = ToolCategory.RECONNAISSANCE.value
