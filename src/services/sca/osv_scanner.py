
from clients.sca.osv_scanner import OSVScannerClient
from repositories.workspace import WorkspaceRepository
from services.base_sca import BaseSCAService

class OSVScannerService(BaseSCAService):
    """Service for OSV-Scanner operations."""
    
    # OSV-Scanner supports multiple languages via lockfiles
    # It doesn't strictly depend on language extensions but rather on lockfiles
    # However, we can hint at supported languages if needed
    SUPPORTED_LANGUAGES = []

    def __init__(self, repository: WorkspaceRepository, client: OSVScannerClient):
        super().__init__(repository, client)
