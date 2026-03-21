"""Amass client for network mapping and attack surface discovery."""

import logging

from clients.base_reconnaissance import BaseReconnaissanceClient

logger = logging.getLogger(__name__)


class AmassClient(BaseReconnaissanceClient):
    """Client for Amass service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "amass")
