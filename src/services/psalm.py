"""Psalm service layer for SAST scanning."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from clients.psalm import PsalmClient
from repositories.workspace import WorkspaceRepository


class PsalmService:
    """Service for Psalm SAST scanning operations."""

    def __init__(self, workspace_repo: WorkspaceRepository, psalm_client: PsalmClient):
        self.workspace_repo = workspace_repo
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
        # Get workspace
        workspace = self.workspace_repo.get(workspace_id)
        if not workspace:
            return {"status": "error", "error": f"Workspace not found: {workspace_id}"}

        workspace_path = workspace.path

        try:
            # Execute scan via client
            result = self.psalm_client.scan(
                workspace_path=str(workspace_path),
                scan_path=scan_path,
                config=config,
            )

            return result

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_latest_report(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get the most recent Psalm report for a workspace.

        Args:
            workspace_id: UUID of the workspace

        Returns:
            Dictionary with report data or error
        """
        # Get workspace
        workspace = self.workspace_repo.get(workspace_id)
        if not workspace:
            return {"status": "error", "error": f"Workspace not found: {workspace_id}"}

        # Find reports directory
        workspace_path = Path(workspace.path)
        reports_dir = workspace_path.parent / "reports" / "sast" / "psalm"

        if not reports_dir.exists():
            return {
                "status": "error",
                "error": "No Psalm reports found for this workspace",
            }

        # Get most recent report
        report_files = sorted(reports_dir.glob("*.sarif"), key=lambda p: p.stat().st_mtime, reverse=True)

        if not report_files:
            return {
                "status": "error",
                "error": "No Psalm reports found for this workspace",
            }

        latest_report = report_files[0]

        try:
            # Read and parse SARIF report
            with open(latest_report, "r") as f:
                report_data = json.load(f)

            # Extract summary information
            finding_count = sum(len(run.get("results", [])) for run in report_data.get("runs", []))

            return {
                "status": "success",
                "report_path": str(latest_report),
                "finding_count": finding_count,
                "report_data": report_data,
            }

        except Exception as e:
            return {"status": "error", "error": f"Failed to read report: {e}"}
