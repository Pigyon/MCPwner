"""Arjun client for HTTP parameter discovery."""

import logging

from clients.base_reconnaissance import BaseReconnaissanceClient

logger = logging.getLogger(__name__)


class ArjunClient(BaseReconnaissanceClient):
    """Client for arjun service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "arjun")
