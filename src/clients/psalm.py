"""Psalm HTTP client for external service communication."""

from clients.base import BaseSASTClient


class PsalmClient(BaseSASTClient):
    """HTTP client for Psalm service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "psalm")
