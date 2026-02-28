"""PMD service for business logic."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from clients.pmd import PMDClient
from config.languages import PMD_LANGUAGES
from repositories.workspace import WorkspaceRepository

logger = logging.getLogger(__name__)


class PMDService:
    """Service for PMD SAST scanning operations."""

    SUPPORTED_LANGUAGES = PMD_LANGUAGES

    def __init__(self, repository: WorkspaceRepository, pmd_client: PMDClient):
        self.repository = repository
        self.pmd_client = pmd_client

    def scan(
        self,
        workspace_id: str,
        scan_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute PMD scan on a workspace.

        Args:
            workspace_id: UUID of the workspace to scan
            scan_path: Optional relative path within workspace to scan
            config: Optional PMD configuration (rulesets, language, exclude patterns)

        Returns:
            Dictionary with scan results including finding count and report path
        """
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

        if scan_path:
            full_scan_path = Path(workspace_path) / scan_path
            if not full_scan_path.exists():
                return {
                    "status": "error",
                    "error": f"Scan path not found: {scan_path}",
                    "error_code": "SCAN_PATH_NOT_FOUND",
                }

        try:
            logger.info(f"Executing PMD scan on workspace {workspace_id}, path: {workspace_path}")
            result = self.pmd_client.scan(
                workspace_path=workspace_path,
                scan_path=scan_path,
                config=config,
            )
            logger.info(f"PMD scan result: status={result.get('status')}, findings={result.get('finding_count', 'N/A')}")
            return result
        except Exception as e:
            logger.error(f"PMD scan failed for workspace {workspace_id}: {e}")
            logger.exception("PMD scan error details")
            return {
                "status": "error",
                "error": f"PMD scan failed: {e}",
                "error_code": "SCAN_FAILED",
            }

    def get_latest_report(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get the most recent PMD report for a workspace.

        Args:
            workspace_id: UUID of the workspace

        Returns:
            Dictionary with report data or error
        """
        workspace = self.repository.find_by_id(workspace_id)
        if not workspace:
            return {
                "status": "error",
                "error": f"Workspace not found: {workspace_id}",
                "error_code": "WORKSPACE_NOT_FOUND",
            }

        report_dir = Path(f"/workspaces/{workspace_id}/reports/sast/pmd")
        if not report_dir.exists():
            return {
                "status": "error",
                "error": f"No PMD reports found for workspace: {workspace_id}",
                "error_code": "NO_REPORTS_FOUND",
            }

        reports = sorted(report_dir.glob("*.sarif"), reverse=True)
        if not reports:
            return {
                "status": "error",
                "error": f"No PMD reports found for workspace: {workspace_id}",
                "error_code": "NO_REPORTS_FOUND",
            }

        latest_report = reports[0]

        try:
            with open(latest_report, "r") as f:
                sarif_data = json.load(f)

            return {
                "status": "success",
                "workspace_id": workspace_id,
                "tool": "pmd",
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
        """Check if language is supported by PMD."""
        return language.lower() in self.SUPPORTED_LANGUAGES
