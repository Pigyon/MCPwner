"""NodeJsScan HTTP client for external service communication."""

from clients.base import BaseSASTClient


class NodeJsScanClient(BaseSASTClient):
    """HTTP client for NodeJsScan service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "nodejsscan")
