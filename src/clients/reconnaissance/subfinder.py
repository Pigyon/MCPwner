"""Subfinder client for subdomain discovery."""

import logging

from clients.base_reconnaissance import BaseReconnaissanceClient

logger = logging.getLogger(__name__)


class SubfinderClient(BaseReconnaissanceClient):
    """Client for Subfinder service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "subfinder")
