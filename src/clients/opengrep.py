"""Opengrep HTTP client for external service communication."""

from clients.base import BaseSASTClient


class OpengrepClient(BaseSASTClient):
    """HTTP client for Opengrep service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "opengrep")
