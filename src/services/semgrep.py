"""Semgrep service for business logic."""

from pathlib import Path
from typing import Any, Dict, Optional

from clients.semgrep import SemgrepClient
from repositories.workspace import WorkspaceRepository


class SemgrepService:
    """Service for Semgrep SAST operations."""

    def __init__(self, repository: WorkspaceRepository, semgrep_client: SemgrepClient):
        self.repository = repository
        self.semgrep_client = semgrep_client

    def scan(
        self,
        workspace_id: str,
        scan_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute Semgrep scan on workspace.

        Args:
            workspace_id: UUID of the workspace to scan
            scan_path: Optional relative path within workspace to scan
            config: Optional Semgrep configuration (rules, exclude patterns)

        Returns:
            Dictionary with scan results including finding count and report path
        """
        # Validate workspace exists
        workspace = self.repository.find_by_id(workspace_id)
        if not workspace:
            return {
                "status": "error",
                "error": f"Workspace not found: {workspace_id}",
                "error_code": "WORKSPACE_NOT_FOUND",
            }

        workspace_path = workspace.path or workspace.local_path
        if not workspace_path:
            return {
                "status": "error",
                "error": f"No source path for workspace: {workspace_id}",
                "error_code": "NO_SOURCE_PATH",
            }

        # Validate scan path if provided
        if scan_path:
            full_scan_path = Path(workspace_path) / scan_path
            if not full_scan_path.exists():
                return {
                    "status": "error",
                    "error": f"Scan path not found: {scan_path}",
                    "error_code": "SCAN_PATH_NOT_FOUND",
                }

        # Execute scan via client
        try:
            result = self.semgrep_client.scan(
                workspace_path=workspace_path, scan_path=scan_path, config=config
            )
            return result
        except Exception as e:
            return {
                "status": "error",
                "error": f"Semgrep scan failed: {e}",
                "error_code": "SCAN_FAILED",
            }

    def get_latest_report(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get the most recent Semgrep report for a workspace.

        Args:
            workspace_id: UUID of the workspace

        Returns:
            Dictionary with report metadata and SARIF content
        """
        workspace = self.repository.find_by_id(workspace_id)
        if not workspace:
            return {
                "status": "error",
                "error": f"Workspace not found: {workspace_id}",
                "error_code": "WORKSPACE_NOT_FOUND",
            }

        # Find most recent report
        report_dir = Path(f"/workspaces/{workspace_id}/reports/sast/semgrep")
        if not report_dir.exists():
            return {
                "status": "error",
                "error": f"No Semgrep reports found for workspace: {workspace_id}",
                "error_code": "NO_REPORTS_FOUND",
            }

        reports = sorted(report_dir.glob("*.sarif"), reverse=True)
        if not reports:
            return {
                "status": "error",
                "error": f"No Semgrep reports found for workspace: {workspace_id}",
                "error_code": "NO_REPORTS_FOUND",
            }

        latest_report = reports[0]

        # Read and parse SARIF
        try:
            import json

            with open(latest_report, "r") as f:
                sarif_data = json.load(f)

            return {
                "status": "success",
                "workspace_id": workspace_id,
                "tool": "semgrep",
                "report_path": str(latest_report),
                "timestamp": latest_report.stem,
                "sarif": sarif_data,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to read report: {e}",
                "error_code": "REPORT_READ_FAILED",
            }

    def is_language_supported(self, language: str) -> bool:
        """
        Check if language is supported by Semgrep.

        Args:
            language: Language name to check

        Returns:
            True if language is supported, False otherwise
        """
        return language.lower() in self.SUPPORTED_LANGUAGES
