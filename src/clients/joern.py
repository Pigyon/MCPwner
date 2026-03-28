"""Joern HTTP client for external service communication."""

from clients.base import BaseSASTClient


class JoernClient(BaseSASTClient):
    """HTTP client for Joern service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "joern")
