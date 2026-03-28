"""bbot client for OSINT automation reconnaissance."""

import logging

from clients.base_reconnaissance import BaseReconnaissanceClient

logger = logging.getLogger(__name__)


class BbotClient(BaseReconnaissanceClient):
    """Client for bbot service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "bbot")
