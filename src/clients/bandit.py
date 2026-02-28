"""Bandit HTTP client for external service communication."""

from clients.base import BaseSASTClient


class BanditClient(BaseSASTClient):
    """HTTP client for Bandit service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "bandit")
