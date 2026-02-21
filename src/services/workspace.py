"""Workspace service for business logic."""

import shutil
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from models import Workspace
from repositories.workspace import WorkspaceRepository
from workspace.local_mount import LocalMountError, setup_local_mount
from workspace.repository import RepositoryError, clone_repository

logger = logging.getLogger(__name__)


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
            created_at=datetime.utcnow(),
        )

        # Handle GitHub clone
        if source_type == "github":
            try:
                repo_path = clone_repository(source, workspace.workspace_id, base_path)
                workspace.path = repo_path
                self.repository.save(workspace)
                logger.info(f"Successfully cloned GitHub repo to {repo_path}")
            except RepositoryError as e:
                logger.error(f"Failed to clone repository: {e}")
                raise

        # Handle local mount
        elif source_type == "local":
            try:
                mount_info = setup_local_mount(source, workspace.workspace_id, base_path)
                
                # Copy local source to shared workspace directory
                # This ensures all containers (CodeQL, SAST) can access the files
                destination_path = mount_info["mount_path"]
                source_path = mount_info["local_path"]
                
                logger.info(f"Copying local files from {source_path} to {destination_path}")
                
                if Path(destination_path).exists():
                    shutil.rmtree(destination_path)
                    
                # Ignore .git directory to save space and time
                shutil.copytree(
                    source_path, 
                    destination_path,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc")
                )
                
                workspace.local_path = source_path
                workspace.mount_path = destination_path
                workspace.path = destination_path
                self.repository.save(workspace)
                logger.info(f"Successfully set up local workspace at {destination_path}")
            except LocalMountError as e:
                logger.error(f"Failed to setup local mount: {e}")
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
