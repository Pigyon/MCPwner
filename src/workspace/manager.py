"""
Workspace Manager - Handles workspace lifecycle management.

This module provides the WorkspaceManager class for creating, listing,
retrieving, and deleting workspaces with UUID-based identification.
"""

import uuid
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .repository import clone_repository, RepositoryError
from .local_mount import setup_local_mount, LocalMountError


class WorkspaceManager:
    """
    Manages workspace lifecycle including creation, listing, retrieval, and deletion.
    
    Workspaces are isolated analysis environments containing either cloned repositories
    or mounted local directories. Each workspace has a unique UUID4 identifier.
    """
    
    def __init__(self):
        """Initialize the WorkspaceManager with an empty workspace registry."""
        self._workspaces: Dict[str, Dict[str, Any]] = {}
        self._databases: Dict[str, List[Dict[str, Any]]] = {}  # workspace_id -> list of databases
        self.max_databases_per_workspace = 10
    
    def create_workspace(
        self,
        source_type: str,
        source: str,
        base_path: str = "/workspaces"
    ) -> Dict[str, str]:
        """
        Create a new workspace with a unique UUID4 identifier.
        
        Args:
            source_type: Type of source ("github" or "local")
            source: GitHub URL or local directory path
            base_path: Base directory for workspaces (default: /workspaces)
            
        Returns:
            Dictionary containing:
                - workspace_id: Unique UUID4 identifier
                - source_type: Type of source
                - source: Source location
                - created_at: ISO 8601 timestamp
                - path: Absolute path to workspace (for github source_type)
                - local_path: Original local path (for local source_type)
                - mount_path: Container mount path (for local source_type)
                
        Raises:
            RepositoryError: If GitHub cloning fails
            LocalMountError: If local path validation fails
        """
        workspace_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"
        
        workspace_metadata = {
            "workspace_id": workspace_id,
            "source_type": source_type,
            "source": source,
            "created_at": created_at
        }
        
        # Clone repository if source type is GitHub
        if source_type == "github":
            try:
                repo_path = clone_repository(source, workspace_id, base_path)
                workspace_metadata["path"] = repo_path
            except RepositoryError as e:
                # Don't store workspace if clone fails
                raise
        
        # Setup local mount if source type is local
        elif source_type == "local":
            try:
                mount_info = setup_local_mount(source, workspace_id, base_path)
                workspace_metadata["local_path"] = mount_info["local_path"]
                workspace_metadata["mount_path"] = mount_info["mount_path"]
                workspace_metadata["path"] = mount_info["local_path"]  # For compatibility
            except LocalMountError as e:
                # Don't store workspace if validation fails
                raise
        
        self._workspaces[workspace_id] = workspace_metadata
        self._databases[workspace_id] = []  # Initialize empty database list
        
        return workspace_metadata
    
    def list_workspaces(self) -> List[Dict[str, Any]]:
        """
        List all workspace metadata.
        
        Returns:
            List of workspace metadata dictionaries, each containing:
                - workspace_id: Unique identifier
                - source_type: Type of source
                - source: Source location
                - created_at: Creation timestamp
        """
        return list(self._workspaces.values())
    
    def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve workspace metadata by ID.
        
        Args:
            workspace_id: UUID of the workspace to retrieve
            
        Returns:
            Workspace metadata dictionary if found, None otherwise
        """
        return self._workspaces.get(workspace_id)
    
    def delete_workspace(self, workspace_id: str) -> bool:
        """
        Delete a workspace by ID.
        
        Args:
            workspace_id: UUID of the workspace to delete
            
        Returns:
            True if workspace was deleted, False if not found
        """
        if workspace_id in self._workspaces:
            del self._workspaces[workspace_id]
            # Also delete associated databases
            if workspace_id in self._databases:
                del self._databases[workspace_id]
            return True
        return False
    
    def cleanup_workspace(
        self,
        workspace_id: str,
        base_path: str = "/workspaces"
    ) -> Dict[str, Any]:
        """
        Cleanup workspace by deleting its directory.
        
        Removes the workspace directory from disk. Skips cleanup for local
        mounts to preserve user data.
        
        Args:
            workspace_id: UUID of the workspace to cleanup
            base_path: Base directory for workspaces (default: /workspaces)
            
        Returns:
            Dictionary containing:
                - workspace_id: Workspace identifier
                - status: "cleaned" or "skipped"
                - reason: Explanation if skipped
                
        Raises:
            ValueError: If workspace not found
        """
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        # Skip cleanup for local mounts
        if workspace["source_type"] == "local":
            return {
                "workspace_id": workspace_id,
                "status": "skipped",
                "reason": "Local mount - preserving user data"
            }
        
        # Delete workspace directory for GitHub clones
        workspace_dir = Path(base_path) / workspace_id
        if workspace_dir.exists():
            shutil.rmtree(workspace_dir)
        
        # Remove from registry
        self.delete_workspace(workspace_id)
        
        return {
            "workspace_id": workspace_id,
            "status": "cleaned",
            "reason": "GitHub clone removed"
        }
    
    def cleanup_old_workspaces(
        self,
        base_path: str = "/workspaces",
        max_age_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Cleanup old GitHub cloned workspaces.
        
        Removes cloned repositories older than the specified age.
        Preserves local mounts regardless of age.
        
        Args:
            base_path: Base directory for workspaces (default: /workspaces)
            max_age_hours: Maximum age in hours (default: 24)
            
        Returns:
            Dictionary containing:
                - cleaned: List of cleaned workspace IDs
                - skipped: List of skipped workspace IDs
                - total_cleaned: Count of cleaned workspaces
                - total_skipped: Count of skipped workspaces
        """
        now = datetime.utcnow()
        cutoff_time = now - timedelta(hours=max_age_hours)
        
        cleaned = []
        skipped = []
        
        # Iterate over copy of workspace IDs to allow modification during iteration
        for workspace_id in list(self._workspaces.keys()):
            workspace = self._workspaces[workspace_id]
            
            # Skip local mounts
            if workspace["source_type"] == "local":
                skipped.append(workspace_id)
                continue
            
            # Parse creation timestamp
            created_at = datetime.fromisoformat(workspace["created_at"].rstrip("Z"))
            
            # Cleanup if older than cutoff
            if created_at < cutoff_time:
                try:
                    result = self.cleanup_workspace(workspace_id, base_path)
                    if result["status"] == "cleaned":
                        cleaned.append(workspace_id)
                    else:
                        skipped.append(workspace_id)
                except Exception as e:
                    # Log error but continue with other workspaces
                    skipped.append(workspace_id)
        
        return {
            "cleaned": cleaned,
            "skipped": skipped,
            "total_cleaned": len(cleaned),
            "total_skipped": len(skipped)
        }

    def add_database(
        self,
        workspace_id: str,
        database_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add a database to a workspace.
        
        Args:
            workspace_id: UUID of the workspace
            database_metadata: Database metadata dictionary
            
        Returns:
            Database metadata
            
        Raises:
            ValueError: If workspace not found or database limit exceeded
        """
        if workspace_id not in self._workspaces:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        if workspace_id not in self._databases:
            self._databases[workspace_id] = []
        
        # Check database limit
        if len(self._databases[workspace_id]) >= self.max_databases_per_workspace:
            raise ValueError(
                f"Database limit exceeded: maximum {self.max_databases_per_workspace} "
                f"databases per workspace"
            )
        
        self._databases[workspace_id].append(database_metadata)
        return database_metadata
    
    def list_databases(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        List all databases for a workspace.
        
        Args:
            workspace_id: UUID of the workspace
            
        Returns:
            List of database metadata dictionaries
            
        Raises:
            ValueError: If workspace not found
        """
        if workspace_id not in self._workspaces:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        return self._databases.get(workspace_id, [])
    
    def get_database(
        self,
        workspace_id: str,
        database_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific database by ID.
        
        Args:
            workspace_id: UUID of the workspace
            database_id: ID of the database
            
        Returns:
            Database metadata if found, None otherwise
        """
        databases = self._databases.get(workspace_id, [])
        for db in databases:
            if db.get("database_id") == database_id:
                return db
        return None
