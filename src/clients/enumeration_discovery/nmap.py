"""Nmap client for network scanning."""

import logging

from clients.base_enumeration_discovery import BaseEnumerationDiscoveryClient

logger = logging.getLogger(__name__)


class NmapClient(BaseEnumerationDiscoveryClient):
    """Client for Nmap service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "nmap")
