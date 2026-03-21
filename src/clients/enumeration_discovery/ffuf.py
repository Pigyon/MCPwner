"""ffuf client for web fuzzing."""

import logging

from clients.base_enumeration_discovery import BaseEnumerationDiscoveryClient

logger = logging.getLogger(__name__)


class FfufClient(BaseEnumerationDiscoveryClient):
    """Client for ffuf service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "ffuf")
