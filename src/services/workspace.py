"""Workspace service for business logic."""

import logging
import os
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from models import Workspace
from repositories.workspace import WorkspaceRepository
from workspace.git_clone import RepositoryError, clone_repository
from workspace.local_mount import LocalMountError, setup_local_mount

logger = logging.getLogger(__name__)

# Scanner containers run as mixed UIDs (root, scanner, 1000) with cap_drop: ALL,
# so workspace dirs must be world-writable on the shared /workspaces volume.
_SHARED_DIR_MODE = 0o777


def _ensure_shared_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(_SHARED_DIR_MODE)
    return path


def _validate_local_codebase(source: str) -> str:
    """Validate a local codebase path for direct use (no copy).

    Accepts absolute paths or paths starting with ~ (home directory).
    Relative paths are rejected to avoid ambiguity.

    Args:
        source: Path to local codebase directory.

    Returns:
        Normalized absolute path.

    Raises:
        ValueError: If path is invalid, relative, doesn't exist, or is not a directory.
    """
    if not (os.path.isabs(source) or source.startswith("~")):
        raise ValueError(
            f"Path must be absolute or start with ~: {source}. "
            f"Example: /home/user/myproject or ~/myproject"
        )

    expanded = os.path.expanduser(source)
    normalized = os.path.abspath(expanded)

    if not os.path.exists(normalized):
        raise ValueError(f"Local path does not exist: {normalized}")

    if not os.path.isdir(normalized):
        raise ValueError(f"Local path is not a directory: {normalized}")

    if not os.access(normalized, os.R_OK):
        raise ValueError(f"Local path is not readable: {normalized}")

    return normalized


class WorkspaceService:
    """Service for workspace operations."""

    def __init__(self, repository: WorkspaceRepository):
        self.repository = repository

    def create_workspace(
        self, source_type: str, source: str, base_path: str = "/workspaces"
    ) -> Dict[str, Any]:
        """Create a new workspace."""
        logger.info(f"Creating workspace from {source_type}: {source}")
        workspace = Workspace(
            workspace_id=str(uuid.uuid4()),
            source_type=source_type,
            source=source,
            created_at=datetime.now(timezone.utc),
        )

        # Handle virtual workspace (for tools that don't have source code)
        if source_type == "virtual":
            try:
                workspace_dir = str(Path(base_path) / workspace.workspace_id)
                self._finalize_workspace(
                    workspace,
                    base_path,
                    workspace_dir,
                    success_msg=f"Successfully created virtual workspace at {workspace_dir}",
                )
            except Exception as e:
                logger.error(f"Failed to create virtual workspace: {e}")
                raise

        # Handle GitHub clone
        elif source_type == "github":
            try:
                repo_path = clone_repository(source, workspace.workspace_id, base_path)
                self._finalize_workspace(
                    workspace,
                    base_path,
                    repo_path,
                    success_msg=f"Successfully cloned GitHub repo to {repo_path}",
                )
            except RepositoryError as e:
                logger.error(f"Failed to clone repository: {e}")
                raise

        # Handle local mount (Docker-based: copies files to shared volume)
        elif source_type == "local":
            try:
                mount_info = setup_local_mount(source, workspace.workspace_id, base_path)
                destination_path = mount_info["mount_path"]
                source_path = mount_info["local_path"]

                logger.info(f"Copying local files from {source_path} to {destination_path}")

                if Path(destination_path).exists():
                    shutil.rmtree(destination_path)

                # Ignore .git directory to save space and time
                shutil.copytree(
                    source_path,
                    destination_path,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
                )

                self._finalize_workspace(
                    workspace,
                    base_path,
                    destination_path,
                    local_path=source_path,
                    mount_path=destination_path,
                    success_msg=f"Successfully set up local workspace at {destination_path}",
                )
            except LocalMountError as e:
                logger.error(f"Failed to setup local mount: {e}")
                raise

        # Handle local_path (native: points directly at local codebase, no copy)
        elif source_type == "local_path":
            try:
                validated_path = _validate_local_codebase(source)
                self._finalize_workspace(
                    workspace,
                    base_path,
                    validated_path,
                    local_path=validated_path,
                    success_msg=(
                        f"Successfully created local_path workspace pointing to {validated_path}"
                    ),
                )
            except ValueError as e:
                logger.error(f"Failed to setup local_path workspace: {e}")
                raise

        else:
            raise ValueError(
                f"Unknown source_type: {source_type}. Supported: github, local, local_path, virtual"
            )

        return workspace.model_dump()

    def _finalize_workspace(
        self,
        workspace: Workspace,
        base_path: str,
        primary_path: str,
        local_path: str = None,
        mount_path: str = None,
        success_msg: str = None,
    ) -> None:
        """Finalize workspace initialization by setting up shared dirs and saving."""
        workspace_base = _ensure_shared_dir(Path(base_path) / workspace.workspace_id)
        _ensure_shared_dir(workspace_base / "reports")

        workspace.path = primary_path
        if local_path:
            workspace.local_path = local_path
        if mount_path:
            workspace.mount_path = mount_path
        workspace.workspace_base_dir = str(workspace_base)

        self.repository.save(workspace)
        if success_msg:
            logger.info(success_msg)

    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List all workspaces."""
        workspaces = self.repository.find_all()
        return [ws.model_dump() for ws in workspaces]

    def get_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """Get workspace by ID."""
        workspace = self.repository.find_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        return workspace.model_dump()

    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete workspace."""
        return self.repository.delete(workspace_id)

    def _safe_rmtree(self, path: Path, result: Dict[str, Any], success_detail: str) -> None:
        """Remove a directory, recording the outcome on ``result``.

        Sets ``deleted_files`` on success, or ``status='error'`` (and logs) on failure.
        """
        try:
            shutil.rmtree(path)
            result["deleted_files"] = True
            result["details"].append(success_detail)
        except Exception as e:
            result["status"] = "error"
            result["details"].append(f"Failed to delete files: {e}")
            logger.error(f"Failed to delete {path}: {e}")

    def cleanup_workspace(
        self,
        workspace_id: str,
        delete_files: bool = True,
        delete_metadata: bool = False,
        base_path: str = "/workspaces",
    ) -> Dict[str, Any]:
        """
        Cleanup workspace with granular control.

        Args:
            workspace_id: Workspace to cleanup
            delete_files: If True, delete workspace files and reports
            delete_metadata: If True, delete workspace metadata from persistence
            base_path: Base path for workspaces

        Returns:
            Dictionary with cleanup status and details
        """
        workspace = self.repository.find_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")

        result = {
            "workspace_id": workspace_id,
            "status": "success",
            "deleted_files": False,
            "deleted_metadata": False,
            "preserved_metadata": False,
            "details": [],
        }

        # Handle file deletion
        if delete_files:
            if workspace.is_local_mount() or workspace.is_local_path():
                # For local workspaces, only delete the reports/metadata dir, never the user's code
                if workspace.is_local_path() and workspace.workspace_base_dir:
                    ws_base = Path(workspace.workspace_base_dir)
                    if ws_base.exists():
                        self._safe_rmtree(
                            ws_base,
                            result,
                            f"Deleted workspace reports directory: {ws_base} "
                            f"(source code at {workspace.path} preserved)",
                        )
                    else:
                        result["details"].append("No workspace reports directory found to delete")
                else:
                    result["details"].append("Skipped file deletion: Local mount - preserving user data")
                    result["status"] = "partial"
            elif workspace.is_virtual():
                # Virtual workspaces can be safely deleted (only contain reports)
                workspace_dir = Path(base_path) / workspace_id
                if workspace_dir.exists():
                    self._safe_rmtree(
                        workspace_dir, result, f"Deleted virtual workspace directory: {workspace_dir}"
                    )
                else:
                    result["details"].append("No workspace directory found to delete")
            else:
                workspace_dir = Path(base_path) / workspace_id
                if workspace_dir.exists():
                    self._safe_rmtree(
                        workspace_dir, result, f"Deleted workspace directory: {workspace_dir}"
                    )
                else:
                    result["details"].append("No workspace directory found to delete")
        else:
            result["details"].append("File deletion skipped (delete_files=False)")

        # Handle metadata deletion
        if delete_metadata:
            if self.repository.delete(workspace_id):
                result["deleted_metadata"] = True
                result["details"].append("Deleted workspace metadata from persistence layer")
            else:
                result["details"].append("Metadata deletion failed or already deleted")
        else:
            result["preserved_metadata"] = True
            result["details"].append("Workspace metadata preserved for future reference")

        return result

    def cleanup_old_workspaces(
        self, base_path: str = "/workspaces", max_age_hours: int = 24
    ) -> Dict[str, Any]:
        """Cleanup old GitHub cloned workspaces."""
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=max_age_hours)

        cleaned = []
        skipped = []

        for workspace in self.repository.find_all():
            if workspace.is_local_mount() or workspace.is_local_path():
                skipped.append(workspace.workspace_id)
                continue

            if workspace.created_at < cutoff_time:
                try:
                    result = self.cleanup_workspace(
                        workspace.workspace_id,
                        delete_files=True,
                        delete_metadata=True,
                        base_path=base_path,
                    )
                    if result["status"] == "success":
                        cleaned.append(workspace.workspace_id)
                    else:
                        skipped.append(workspace.workspace_id)
                except Exception:
                    skipped.append(workspace.workspace_id)

        return {
            "cleaned": cleaned,
            "skipped": skipped,
            "total_cleaned": len(cleaned),
            "total_skipped": len(skipped),
        }
