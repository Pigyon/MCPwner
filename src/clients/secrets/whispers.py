import logging

from clients.base_secrets import BaseSecretsClient

logger = logging.getLogger(__name__)


class WhispersClient(BaseSecretsClient):
    """Client for Whispers service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "whispers")
