import logging
from typing import Any, Dict, Optional

from clients.base_secrets import BaseSecretsClient

logger = logging.getLogger(__name__)


class GitleaksClient(BaseSecretsClient):
    """Client for Gitleaks service."""

    def __init__(self, service_url: str):
        super().__init__(service_url, "gitleaks")
