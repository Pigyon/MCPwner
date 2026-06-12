"""Base service for Utilities operations."""

from clients.base_utilities import BaseUtilitiesClient
from config.tools import ToolCategory
from repositories.workspace import WorkspaceRepository
from services.base_scan import BaseScanService


class BaseUtilitiesService(BaseScanService):
    """Base service for Utilities operations."""

    def __init__(self, repository: WorkspaceRepository, client: BaseUtilitiesClient):
        super().__init__(repository, client)
        self.tool_category = ToolCategory.UTILITIES.value
