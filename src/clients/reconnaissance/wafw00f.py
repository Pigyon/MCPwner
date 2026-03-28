"""Wafw00f client for Web Application Firewall detection."""

import logging

from clients.base_reconnaissance import BaseReconnaissanceClient

logger = logging.getLogger(__name__)


class Wafw00fClient(BaseReconnaissanceClient):
    """Client for wafw00f service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "wafw00f")
