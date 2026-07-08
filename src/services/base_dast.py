"""Base service for DAST operations."""

from clients.base_dast import BaseDastClient
from config.tools import ToolCategory
from repositories.workspace import WorkspaceRepository
from services.base_scan import BaseScanService


class BaseDastService(BaseScanService):
    """Base service for DAST operations."""

    def __init__(self, repository: WorkspaceRepository, client: BaseDastClient):
        super().__init__(repository, client)
        self.tool_category = ToolCategory.DAST.value
