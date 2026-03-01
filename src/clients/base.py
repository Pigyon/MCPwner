import logging
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class BaseScanClient:
    """Base HTTP client for scan services (SAST, SCA, etc.)."""

    def __init__(self, service_url: str, tool_name: str):
        self.service_url = service_url.rstrip("/")
        self.tool_name = tool_name

    def scan(
        self,
        workspace_path: str,
        scan_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute scan via HTTP.

        Args:
            workspace_path: Path to the workspace directory
            scan_path: Optional relative path within workspace to scan
            config: Optional configuration (rules, exclude patterns)

        Returns:
            Dictionary with scan results including finding count and report path
        """
        payload = {"workspace_path": workspace_path}
        if scan_path:
            payload["scan_path"] = scan_path
        if config:
            payload["config"] = config

        logger.info(f"Sending scan request to {self.service_url}/scan with payload: {payload}")
        try:
            response = requests.post(f"{self.service_url}/scan", json=payload, timeout=600)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to {self.tool_name} service at {self.service_url}: {e}")
            raise RuntimeError(
                f"Cannot connect to {self.tool_name} service at {self.service_url}. "
                f"Is the {self.tool_name} container running? Check with: docker ps | grep {self.tool_name}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.tool_name} scan request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def get_version(self) -> Dict[str, Any]:
        """Get tool version via HTTP."""
        response = requests.get(f"{self.service_url}/version", timeout=10)
        response.raise_for_status()
        return response.json()


class BaseSASTClient(BaseScanClient):
    """Base HTTP client for SAST services."""

    pass


class BaseSCAClient(BaseScanClient):
    """Base HTTP client for SCA services."""

    pass
