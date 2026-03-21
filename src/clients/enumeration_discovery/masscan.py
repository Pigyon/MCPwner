"""Masscan client for fast port scanning."""

import logging

from clients.base_enumeration_discovery import BaseEnumerationDiscoveryClient

logger = logging.getLogger(__name__)


class MasscanClient(BaseEnumerationDiscoveryClient):
    """Client for Masscan service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "masscan")
