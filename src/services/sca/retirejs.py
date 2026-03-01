from clients.sca.retirejs import RetireJSClient
from config.languages import JAVASCRIPT_LANGUAGES
from repositories.workspace import WorkspaceRepository
from services.base_sca import BaseSCAService


class RetireJSService(BaseSCAService):
    """Service for Retire.js operations."""

    SUPPORTED_LANGUAGES = JAVASCRIPT_LANGUAGES

    def __init__(self, repository: WorkspaceRepository, client: RetireJSClient):
        super().__init__(repository, client)
