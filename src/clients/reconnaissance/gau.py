"""gau client for fetching URLs from web archives."""

import logging

from clients.base_reconnaissance import BaseReconnaissanceClient

logger = logging.getLogger(__name__)


class GauClient(BaseReconnaissanceClient):
    """Client for gau service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "gau")
