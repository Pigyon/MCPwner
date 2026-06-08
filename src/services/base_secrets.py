from clients.base_secrets import BaseSecretsClient
from repositories.workspace import WorkspaceRepository
from services.base_scan import BaseScanService


class BaseSecretsService(BaseScanService):
    """Base service for Secrets operations."""

    def __init__(self, repository: WorkspaceRepository, client: BaseSecretsClient):
        super().__init__(repository, client)
        self.tool_category = "secrets"
