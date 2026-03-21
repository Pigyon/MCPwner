"""Base service for Enumeration & Discovery operations."""

from clients.base_enumeration_discovery import BaseEnumerationDiscoveryClient
from repositories.workspace import WorkspaceRepository
from services.base_static import BaseStaticService


class BaseEnumerationDiscoveryService(BaseStaticService):
    """Base service for Enumeration & Discovery operations."""

    def __init__(self, repository: WorkspaceRepository, client: BaseEnumerationDiscoveryClient):
        super().__init__(repository, client)
        self.tool_category = "enumeration_discovery"
