"""Workspace service for business logic."""

import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from models import Workspace
from repositories.workspace import WorkspaceRepository
from workspace.local_mount import LocalMountError, setup_local_mount
from workspace.repository import RepositoryError, clone_repository


class WorkspaceService:
    """Service for workspace operations."""

    def __init__(self, repository: WorkspaceRepository):
        self.repository = repository

    def create_workspace(
        self, source_type: str, source: str, base_path: str = "/workspaces"
    ) -> Dict[str, Any]:
        """Create a new workspace."""
        workspace = Workspace(
            workspace_id=str(uuid.uuid4()),
            source_type=source_type,
            source=source,
            created_at=datetime.utcnow(),
        )

        # Handle GitHub clone
        if source_type == "github":
            try:
                repo_path = clone_repository(source, workspace.workspace_id, base_path)
                workspace.path = repo_path
                self.repository.save(workspace)
            except RepositoryError:
                raise

        # Handle local mount
        elif source_type == "local":
            try:
                mount_info = setup_local_mount(source, workspace.workspace_id, base_path)
                workspace.local_path = mount_info["local_path"]
                workspace.mount_path = mount_info["mount_path"]
                workspace.path = mount_info["local_path"]
                self.repository.save(workspace)
            except LocalMountError:
                raise

        return workspace.model_dump()

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

    def cleanup_workspace(self, workspace_id: str, base_path: str = "/workspaces") -> Dict[str, Any]:
        """Cleanup workspace directory."""
        workspace = self.repository.find_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")

        if workspace.is_local_mount():
            return {
                "workspace_id": workspace_id,
                "status": "skipped",
                "reason": "Local mount - preserving user data",
            }

        workspace_dir = Path(base_path) / workspace_id
        if workspace_dir.exists():
            shutil.rmtree(workspace_dir)

        self.repository.delete(workspace_id)

        return {
            "workspace_id": workspace_id,
            "status": "cleaned",
            "reason": "GitHub clone removed",
        }

    def cleanup_old_workspaces(
        self, base_path: str = "/workspaces", max_age_hours: int = 24
    ) -> Dict[str, Any]:
        """Cleanup old GitHub cloned workspaces."""
        now = datetime.utcnow()
        cutoff_time = now - timedelta(hours=max_age_hours)

        cleaned = []
        skipped = []

        for workspace in self.repository.find_all():
            if workspace.is_local_mount():
                skipped.append(workspace.workspace_id)
                continue

            if workspace.created_at < cutoff_time:
                try:
                    result = self.cleanup_workspace(workspace.workspace_id, base_path)
                    if result["status"] == "cleaned":
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
