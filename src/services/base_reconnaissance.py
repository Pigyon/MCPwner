"""Base service for Reconnaissance operations."""

from clients.base_reconnaissance import BaseReconnaissanceClient
from repositories.workspace import WorkspaceRepository
from services.base_static import BaseStaticService


class BaseReconnaissanceService(BaseStaticService):
    """Base service for Reconnaissance operations."""

    def __init__(self, repository: WorkspaceRepository, client: BaseReconnaissanceClient):
        super().__init__(repository, client)
        self.tool_category = "reconnaissance"
