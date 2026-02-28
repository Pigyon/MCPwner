"""Psalm service for business logic."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from clients.psalm import PsalmClient
from config.languages import PSALM_LANGUAGES
from repositories.workspace import WorkspaceRepository

logger = logging.getLogger(__name__)


class PsalmService:
    """Service for Psalm SAST scanning operations."""

    SUPPORTED_LANGUAGES = PSALM_LANGUAGES

    def __init__(self, repository: WorkspaceRepository, psalm_client: PsalmClient):
        self.repository = repository
        self.psalm_client = psalm_client

    def scan(
        self,
        workspace_id: str,
        scan_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute Psalm scan on a workspace.

        Args:
            workspace_id: UUID of the workspace to scan
            scan_path: Optional relative path within workspace to scan
            config: Optional Psalm configuration (error_level, etc.)

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
            logger.info(f"Executing Psalm scan on workspace {workspace_id}, path: {workspace_path}")
            result = self.psalm_client.scan(
                workspace_path=workspace_path,
                scan_path=scan_path,
                config=config,
            )
            logger.info(f"Psalm scan result: status={result.get('status')}, findings={result.get('finding_count', 'N/A')}")
            return result
        except Exception as e:
            logger.error(f"Psalm scan failed for workspace {workspace_id}: {e}")
            logger.exception("Psalm scan error details")
            return {
                "status": "error",
                "error": f"Psalm scan failed: {e}",
                "error_code": "SCAN_FAILED",
            }

    def get_latest_report(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get the most recent Psalm report for a workspace.

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

        report_dir = Path(f"/workspaces/{workspace_id}/reports/sast/psalm")
        if not report_dir.exists():
            return {
                "status": "error",
                "error": f"No Psalm reports found for workspace: {workspace_id}",
                "error_code": "NO_REPORTS_FOUND",
            }

        reports = sorted(report_dir.glob("*.sarif"), reverse=True)
        if not reports:
            return {
                "status": "error",
                "error": f"No Psalm reports found for workspace: {workspace_id}",
                "error_code": "NO_REPORTS_FOUND",
            }

        latest_report = reports[0]

        try:
            with open(latest_report, "r") as f:
                sarif_data = json.load(f)

            return {
                "status": "success",
                "workspace_id": workspace_id,
                "tool": "psalm",
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
        """Check if language is supported by Psalm."""
        return language.lower() in self.SUPPORTED_LANGUAGES
