"""Katana client for web crawling and URL extraction."""

import logging

from clients.base_reconnaissance import BaseReconnaissanceClient

logger = logging.getLogger(__name__)


class KatanaClient(BaseReconnaissanceClient):
    """Client for katana service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "katana")
