"""Base service for SAST operations."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from clients.base import BaseSASTClient
from repositories.workspace import WorkspaceRepository

logger = logging.getLogger(__name__)


class BaseSASTService:
    """Base service for SAST operations."""

    SUPPORTED_LANGUAGES: List[str] = []

    def __init__(self, repository: WorkspaceRepository, client: BaseSASTClient):
        self.repository = repository
        self.client = client
        self.tool_name = client.tool_name

    def scan(
        self,
        workspace_id: str,
        scan_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute scan on workspace.

        Args:
            workspace_id: UUID of the workspace to scan
            scan_path: Optional relative path within workspace to scan
            config: Optional configuration (rules, exclude patterns)

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
            logger.info(f"Executing {self.tool_name} scan on workspace {workspace_id}, path: {workspace_path}")
            result = self.client.scan(
                workspace_path=workspace_path, scan_path=scan_path, config=config
            )
            logger.info(f"{self.tool_name} scan result: status={result.get('status')}, findings={result.get('finding_count', 'N/A')}")
            return result
        except Exception as e:
            logger.error(f"{self.tool_name} scan failed for workspace {workspace_id}: {e}")
            logger.exception(f"{self.tool_name} scan error details")
            return {
                "status": "error",
                "error": f"{self.tool_name} scan failed: {e}",
                "error_code": "SCAN_FAILED",
            }

    def get_latest_report(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get the most recent report for a workspace.

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
        report_dir = Path(f"/workspaces/{workspace_id}/reports/sast/{self.tool_name}")
        
        if not report_dir.exists():
            return {
                "status": "error",
                "error": f"No {self.tool_name} reports found for workspace: {workspace_id}",
                "error_code": "NO_REPORTS_FOUND",
            }

        reports = sorted(list(report_dir.glob("*.sarif")) + list(report_dir.glob("*.json")), reverse=True)
        if not reports:
            return {
                "status": "error",
                "error": f"No {self.tool_name} reports found for workspace: {workspace_id}",
                "error_code": "NO_REPORTS_FOUND",
            }

        latest_report = reports[0]

        # Read and parse SARIF or JSON
        try:
            with open(latest_report, "r") as f:
                report_data = json.load(f)

            return {
                "status": "success",
                "workspace_id": workspace_id,
                "tool": self.tool_name,
                "report_path": str(latest_report),
                "timestamp": latest_report.stem,
                "sarif": report_data, # we will always prefer and pre-configure sarif, though it might be raw JSON
                "report_content": report_data 
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to read report: {e}",
                "error_code": "REPORT_READ_FAILED",
            }

    def is_language_supported(self, language: str) -> bool:
        """
        Check if language is supported.

        Args:
            language: Language name to check

        Returns:
            True if language is supported, False otherwise
        """
        return language.lower() in self.SUPPORTED_LANGUAGES
