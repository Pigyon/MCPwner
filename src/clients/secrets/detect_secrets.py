import logging

from clients.base_secrets import BaseSecretsClient

logger = logging.getLogger(__name__)


class DetectSecretsClient(BaseSecretsClient):
    """Client for Detect-Secrets service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "detect-secrets")
