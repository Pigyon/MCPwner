"""Gosec HTTP client for external service communication."""

from clients.base import BaseSASTClient


class GosecClient(BaseSASTClient):
    """HTTP client for Gosec service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "gosec")
