
from clients.sca.grype import GrypeClient
from repositories.workspace import WorkspaceRepository
from services.base_sca import BaseSCAService

class GrypeService(BaseSCAService):
    """Service for Grype operations."""
    
    # Grype supports most languages/filesystems
    SUPPORTED_LANGUAGES = []

    def __init__(self, repository: WorkspaceRepository, client: GrypeClient):
        super().__init__(repository, client)
