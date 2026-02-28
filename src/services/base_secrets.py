from clients.base_secrets import BaseSecretsClient
from repositories.workspace import WorkspaceRepository
from services.base_static import BaseStaticService


class BaseSecretsService(BaseStaticService):
    """Base service for Secrets operations."""

    def __init__(self, repository: WorkspaceRepository, client: BaseSecretsClient):
        super().__init__(repository, client)
        self.tool_category = "secrets"
