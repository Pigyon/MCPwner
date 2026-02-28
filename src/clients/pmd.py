"""PMD HTTP client for external service communication."""

from clients.base import BaseSASTClient


class PMDClient(BaseSASTClient):
    """HTTP client for PMD service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "pmd")
