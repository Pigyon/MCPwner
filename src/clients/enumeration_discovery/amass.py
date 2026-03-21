"""Amass client for network mapping and attack surface discovery."""

import logging

from clients.base_enumeration_discovery import BaseEnumerationDiscoveryClient

logger = logging.getLogger(__name__)


class AmassClient(BaseEnumerationDiscoveryClient):
    """Client for Amass service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "amass")
