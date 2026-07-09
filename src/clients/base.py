import logging
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

# Scan timeout stays under typical ~60s MCP limits so long scans background cleanly.
SCAN_TIMEOUT_SECONDS = 50
# Joern cold-starts ~16s; allow headroom when many /version probes run in parallel.
VERSION_TIMEOUT_SECONDS = 45
# The /health endpoint is static (no CLI invocation), so a tight timeout is fine.
HEALTH_TIMEOUT_SECONDS = 10
LIST_REPORTS_TIMEOUT_SECONDS = 30
GET_REPORT_TIMEOUT_SECONDS = 60


class BaseClient:
    """Base HTTP client with version and health endpoints."""

    def __init__(self, service_url: str, tool_name: str):
        self.service_url = service_url.rstrip("/")
        self.tool_name = tool_name

    def _get(
        self, endpoint: str, timeout_seconds: int, params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Send GET request and handle connection errors."""
        try:
            response = requests.get(
                f"{self.service_url}{endpoint}", params=params, timeout=timeout_seconds
            )
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to {self.tool_name} service at {self.service_url}: {e}")
            raise RuntimeError(
                f"Cannot connect to {self.tool_name} service at {self.service_url}. "
                f"Is the {self.tool_name} container running? "
                f"Check with: docker ps | grep {self.tool_name}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.tool_name} request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def get_version(self) -> Dict[str, Any]:
        """Get tool version via HTTP."""
        response = self._get("/version", VERSION_TIMEOUT_SECONDS)
        return response.json()

    def _post_with_background_timeout(
        self,
        endpoint: str,
        payload: dict,
        timeout_seconds: int,
        background_message: str,
        background_extra: dict,
    ) -> Dict[str, Any]:
        """Send POST request and handle background timeout."""
        try:
            response = requests.post(
                f"{self.service_url}{endpoint}", json=payload, timeout=timeout_seconds
            )
            if not response.ok:
                body = response.text[:500]
                raise RuntimeError(
                    f"{self.tool_name} service returned HTTP {response.status_code}: {body}"
                )
            return response.json()
        except requests.exceptions.ReadTimeout:
            logger.warning(
                f"{self.tool_name} request exceeded {timeout_seconds}s timeout. "
                "It is likely still running in the background."
            )
            res = {
                "status": "backgrounded",
                "message": background_message,
            }
            res.update(background_extra)
            return res
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to {self.tool_name} service at {self.service_url}: {e}")
            raise RuntimeError(
                f"Cannot connect to {self.tool_name} service at {self.service_url}. "
                f"Is the {self.tool_name} container running? "
                f"Check with: docker ps | grep {self.tool_name}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.tool_name} request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def get_health(self) -> Dict[str, Any]:
        """Liveness check via the cheap static /health endpoint.

        Unlike /version, this does not execute the tool's CLI, so it stays fast and
        reliable even while the CLI is slow to cold-start.
        """
        response = self._get("/health", HEALTH_TIMEOUT_SECONDS)
        return response.json()


class BaseScanClient(BaseClient):
    """Base HTTP client for scan services (SAST, SCA, etc.)."""

    # Name of the MCP tool used to retrieve this category's reports. Overridden
    # per category so backgrounded-scan hints point at the correct tool.
    report_tool: str = "the matching get_report"

    def __init__(self, service_url: str, tool_name: str, category: str):
        super().__init__(service_url, tool_name)
        self.report_tool = f"get_{category}_report"

    def scan(
        self,
        workspace_path: str,
        scan_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        report_base: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute scan via HTTP.

        Args:
            workspace_path: Path to the workspace directory
            scan_path: Optional relative path within workspace to scan
            config: Optional configuration (rules, exclude patterns)
            report_base: Optional override for report output base directory

        Returns:
            Dictionary with scan results including finding count and report path
        """
        payload = {"workspace_path": workspace_path}
        if scan_path:
            payload["scan_path"] = scan_path
        payload["config"] = config if config is not None else {}
        if report_base:
            payload["report_base"] = report_base

        timeout_seconds = (
            config.get("mcp_timeout", SCAN_TIMEOUT_SECONDS) if config else SCAN_TIMEOUT_SECONDS
        )

        logger.info(f"Sending scan request to {self.service_url}/scan with payload: {payload}")
        return self._post_with_background_timeout(
            "/scan",
            payload,
            timeout_seconds,
            f"Scan exceeded {timeout_seconds}s MCP timeout and is continuing in the background.",
            {"next_steps": f"Use the {self.report_tool} tool later to check if the report is ready."},
        )

    def list_reports(self, workspace_path: str, report_base: Optional[str] = None) -> Dict[str, Any]:
        """List available report timestamps via HTTP."""
        try:
            params = {"workspace_path": workspace_path}
            if report_base:
                params["report_base"] = report_base
            response = self._get("/reports", LIST_REPORTS_TIMEOUT_SECONDS, params=params)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.tool_name} list_reports failed: {e}")
            return {"status": "error", "error": str(e), "reports": []}

    def get_report(
        self, workspace_path: str, timestamp: str, report_base: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve a specific report by timestamp via HTTP."""
        try:
            params = {"workspace_path": workspace_path}
            if report_base:
                params["report_base"] = report_base
            response = self._get(f"/report/{timestamp}", GET_REPORT_TIMEOUT_SECONDS, params=params)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.tool_name} get_report failed: {e}")
            return {"status": "error", "error": str(e)}
