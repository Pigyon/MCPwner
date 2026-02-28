"""Brakeman HTTP client for external service communication."""

from clients.base import BaseSASTClient


class BrakemanClient(BaseSASTClient):
    """HTTP client for Brakeman service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "brakeman")
