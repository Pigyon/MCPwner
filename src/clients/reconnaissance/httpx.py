"""httpx client for HTTP probing and analysis."""

import logging

from clients.base_reconnaissance import BaseReconnaissanceClient

logger = logging.getLogger(__name__)


class HttpxClient(BaseReconnaissanceClient):
    """Client for httpx service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "httpx")
