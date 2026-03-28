"""YASA HTTP client for external service communication."""

from clients.base import BaseSASTClient


class YASAClient(BaseSASTClient):
    """HTTP client for YASA service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "yasa")
