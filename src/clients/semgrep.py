"""Semgrep HTTP client for external service communication."""

from clients.base import BaseSASTClient


class SemgrepClient(BaseSASTClient):
    """HTTP client for Semgrep service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "semgrep")
