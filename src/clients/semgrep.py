"""Semgrep HTTP client for external service communication."""

from typing import Any, Dict, Optional

import requests


class SemgrepClient:
    """HTTP client for Semgrep service."""

    def __init__(self, service_url: str):
        self.service_url = service_url.rstrip("/")

    def scan(
        self,
        workspace_path: str,
        scan_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute Semgrep scan via HTTP.

        Args:
            workspace_path: Path to the workspace directory
            scan_path: Optional relative path within workspace to scan
            config: Optional Semgrep configuration (rules, exclude patterns)

        Returns:
            Dictionary with scan results including finding count and report path
        """
        payload = {"workspace_path": workspace_path}
        if scan_path:
            payload["scan_path"] = scan_path
        if config:
            payload["config"] = config

        response = requests.post(f"{self.service_url}/scan", json=payload, timeout=600)
        response.raise_for_status()
        return response.json()

    def get_version(self) -> Dict[str, Any]:
        """Get Semgrep version via HTTP."""
        response = requests.get(f"{self.service_url}/version", timeout=10)
        response.raise_for_status()
        return response.json()
