from clients.sca.syft import SyftClient
from repositories.workspace import WorkspaceRepository
from services.base_sca import BaseSCAService


class SyftService(BaseSCAService):
    """Service for Syft operations."""

    # Syft supports most languages/filesystems
    SUPPORTED_LANGUAGES = []

    def __init__(self, repository: WorkspaceRepository, client: SyftClient):
        super().__init__(repository, client)
