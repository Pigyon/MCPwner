"""Base static analysis service."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from repositories.workspace import WorkspaceRepository

logger = logging.getLogger(__name__)


class BaseStaticService:
    """Base service for Static Analysis operations (SAST, Secrets, etc.)."""

    def __init__(self, repository: WorkspaceRepository, client: Any):
        self.repository = repository
        self.client = client
        self.tool_name = client.tool_name
        # Category of the tool (sast, secrets, etc.) - should be set by subclass or inferred
        self.tool_category = "sast"
        # Cache of last scan result per workspace for reliable report retrieval
        self._last_scan_results: Dict[str, Dict[str, Any]] = {}

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
            logger.info(
                f"Executing {self.tool_name} scan on workspace {workspace_id}, path: {workspace_path}"
            )
            # For local_path workspaces, pass report_base so containers write reports
            # to the workspace base dir instead of deriving from workspace_path
            report_base = None
            if workspace.is_local_path() and workspace.workspace_base_dir:
                report_base = workspace.workspace_base_dir

            result = self.client.scan(
                workspace_path=workspace_path,
                scan_path=scan_path,
                config=config,
                report_base=report_base,
            )
            logger.info(
                f"{self.tool_name} scan result: status={result.get('status')}, "
                f"findings={result.get('finding_count', 'N/A')}"
            )
            # Cache scan result for reliable report retrieval
            if result.get("status") == "success":
                self._last_scan_results[workspace_id] = {
                    "workspace_path": workspace_path,
                    "report_path": result.get("report_path"),
                    "timestamp": result.get("timestamp"),
                }
                # Persist to disk for cross-restart reliability
                self._persist_scan_result(workspace_id)
            return result
        except Exception as e:
            logger.error(f"{self.tool_name} scan failed for workspace {workspace_id}: {e}")
            logger.exception(f"{self.tool_name} scan error details")
            return {
                "status": "error",
                "error": f"{self.tool_name} scan failed: {e}",
                "error_code": "SCAN_FAILED",
            }

    def _get_reports_base(self, workspace_id: str) -> str:
        """Get the base directory for reports for a given workspace.

        Uses workspace.get_reports_base_dir() if available, falls back to /workspaces/{id}.
        """
        workspace = self.repository.find_by_id(workspace_id)
        if workspace:
            return workspace.get_reports_base_dir()
        return f"/workspaces/{workspace_id}"

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

        # Find most recent report on the shared filesystem
        reports_base = self._get_reports_base(workspace_id)
        report_dir = Path(f"{reports_base}/reports/{self.tool_category}/{self.tool_name}")

        if report_dir.exists():
            all_entries = list(report_dir.iterdir())
            logger.info(
                f"Report dir {report_dir} exists with {len(all_entries)} entries: "
                f"{[e.name for e in all_entries[:10]]}"
            )
            reports = sorted(
                list(report_dir.glob("*.sarif")) + list(report_dir.glob("*.json")), reverse=True
            )
            if reports:
                latest_report = reports[0]
                try:
                    with open(latest_report, "r") as f:
                        report_data = json.load(f)

                    return {
                        "status": "success",
                        "workspace_id": workspace_id,
                        "tool": self.tool_name,
                        "report_path": str(latest_report),
                        "timestamp": latest_report.stem,
                        "sarif": report_data,
                        "report_content": report_data,
                    }
                except Exception as e:
                    logger.warning(f"Failed to read local report {latest_report}: {e}")
            else:
                logger.warning(f"Report dir exists but no .sarif/.json files found in {report_dir}")
        else:
            logger.warning(f"Report dir does not exist: {report_dir}")

        # Fallback 2: use cached scan result to read report directly
        cached = self._load_scan_result(workspace_id)
        logger.info(f"Fallback 2: cached scan result for {workspace_id}: {cached}")
        if cached and cached.get("report_path"):
            cached_path = Path(cached["report_path"])
            if cached_path.exists():
                try:
                    with open(cached_path, "r") as f:
                        report_data = json.load(f)
                    return {
                        "status": "success",
                        "workspace_id": workspace_id,
                        "tool": self.tool_name,
                        "report_path": str(cached_path),
                        "timestamp": cached.get("timestamp", cached_path.stem),
                        "sarif": report_data,
                        "report_content": report_data,
                    }
                except Exception as e:
                    logger.warning(f"Failed to read cached report path {cached_path}: {e}")

        # Fallback 3: fetch report via the tool container's HTTP API
        workspace_path = workspace.path or workspace.local_path
        if workspace_path and hasattr(self.client, "list_reports"):
            try:
                report_base = None
                if workspace.is_local_path() and workspace.workspace_base_dir:
                    report_base = workspace.workspace_base_dir
                listing = self.client.list_reports(workspace_path, report_base=report_base)
                timestamps = listing.get("reports", [])
                if timestamps:
                    result = self.client.get_report(
                        workspace_path, timestamps[0], report_base=report_base
                    )
                    if result.get("status") == "success":
                        report_data = result.get("report") or result.get("report_raw", "")
                        return {
                            "status": "success",
                            "workspace_id": workspace_id,
                            "tool": self.tool_name,
                            "report_path": result.get("report_path", ""),
                            "timestamp": timestamps[0],
                            "sarif": report_data if isinstance(report_data, dict) else None,
                            "report_content": report_data,
                        }
            except Exception as e:
                logger.warning(f"HTTP fallback for {self.tool_name} report failed: {e}")

        return {
            "status": "error",
            "error": f"No {self.tool_name} reports found for workspace: {workspace_id}",
            "error_code": "NO_REPORTS_FOUND",
        }

    def _scan_cache_path(self, workspace_id: str) -> Path:
        """Path to the on-disk scan result cache file."""
        reports_base = self._get_reports_base(workspace_id)
        return Path(f"{reports_base}/reports/{self.tool_category}/{self.tool_name}/.last_scan.json")

    def _persist_scan_result(self, workspace_id: str) -> None:
        """Write the cached scan result to disk."""
        cached = self._last_scan_results.get(workspace_id)
        if not cached:
            return
        try:
            cache_file = self._scan_cache_path(workspace_id)
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, "w") as f:
                json.dump(cached, f)
        except Exception as e:
            logger.warning(f"Failed to persist scan cache for {workspace_id}: {e}")

    def _load_scan_result(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Load a previously persisted scan result from disk."""
        # Check in-memory first
        if workspace_id in self._last_scan_results:
            return self._last_scan_results[workspace_id]
        # Try disk
        try:
            cache_file = self._scan_cache_path(workspace_id)
            if cache_file.exists():
                with open(cache_file) as f:
                    data = json.load(f)
                self._last_scan_results[workspace_id] = data
                return data
        except Exception as e:
            logger.warning(f"Failed to load scan cache for {workspace_id}: {e}")
        return None
