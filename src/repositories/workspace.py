"""Workspace repository for data persistence."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from models import CodeQLDatabase, Workspace

logger = logging.getLogger(__name__)


class WorkspaceRepository:
    """File-based workspace repository with automatic persistence."""

    def __init__(self, storage_path: str = "/workspaces/.metadata"):
        """
        Initialize repository with file-based storage.
        
        Args:
            storage_path: Path to store metadata files (default: /workspaces/.metadata)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.workspaces_file = self.storage_path / "workspaces.json"
        self.databases_file = self.storage_path / "databases.json"
        
        # In-memory cache for performance
        self._workspaces: Dict[str, Workspace] = {}
        self._databases: Dict[str, List[CodeQLDatabase]] = {}
        
        # Load existing data on initialization
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load workspace and database metadata from disk."""
        try:
            # Load workspaces
            if self.workspaces_file.exists():
                with open(self.workspaces_file, 'r') as f:
                    data = json.load(f)
                    self._workspaces = {
                        ws_id: Workspace(**ws_data) 
                        for ws_id, ws_data in data.items()
                    }
                logger.info(f"Loaded {len(self._workspaces)} workspaces from disk")
            
            # Load databases
            if self.databases_file.exists():
                with open(self.databases_file, 'r') as f:
                    data = json.load(f)
                    self._databases = {
                        ws_id: [CodeQLDatabase(**db_data) for db_data in db_list]
                        for ws_id, db_list in data.items()
                    }
                logger.info(f"Loaded database metadata for {len(self._databases)} workspaces")
        except Exception as e:
            logger.error(f"Failed to load metadata from disk: {e}")
            # Continue with empty state if load fails

    def _save_workspaces_to_disk(self) -> None:
        """Save workspaces to disk atomically."""
        try:
            # Write to temporary file first
            temp_file = self.workspaces_file.with_suffix('.tmp')
            data = {
                ws_id: workspace.model_dump()
                for ws_id, workspace in self._workspaces.items()
            }
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic rename
            temp_file.replace(self.workspaces_file)
            logger.debug(f"Saved {len(self._workspaces)} workspaces to disk")
        except Exception as e:
            logger.error(f"Failed to save workspaces to disk: {e}")

    def _save_databases_to_disk(self) -> None:
        """Save databases to disk atomically."""
        try:
            # Write to temporary file first
            temp_file = self.databases_file.with_suffix('.tmp')
            data = {
                ws_id: [db.model_dump() for db in db_list]
                for ws_id, db_list in self._databases.items()
            }
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic rename
            temp_file.replace(self.databases_file)
            logger.debug(f"Saved database metadata for {len(self._databases)} workspaces")
        except Exception as e:
            logger.error(f"Failed to save databases to disk: {e}")

    def save(self, workspace: Workspace) -> None:
        """Save workspace to memory and disk."""
        self._workspaces[workspace.workspace_id] = workspace
        if workspace.workspace_id not in self._databases:
            self._databases[workspace.workspace_id] = []
        self._save_workspaces_to_disk()

    def find_by_id(self, workspace_id: str) -> Optional[Workspace]:
        """Find workspace by ID."""
        return self._workspaces.get(workspace_id)

    def find_all(self) -> List[Workspace]:
        """Find all workspaces."""
        return list(self._workspaces.values())

    def delete(self, workspace_id: str) -> bool:
        """Delete workspace from memory and disk."""
        if workspace_id in self._workspaces:
            del self._workspaces[workspace_id]
            if workspace_id in self._databases:
                del self._databases[workspace_id]
            self._save_workspaces_to_disk()
            self._save_databases_to_disk()
            return True
        return False

    def save_database(self, database: CodeQLDatabase) -> None:
        """Save database metadata to memory and disk."""
        if database.workspace_id not in self._databases:
            self._databases[database.workspace_id] = []

        # Update existing or append new
        databases = self._databases[database.workspace_id]
        for i, db in enumerate(databases):
            if db.database_id == database.database_id:
                databases[i] = database
                self._save_databases_to_disk()
                return
        databases.append(database)
        self._save_databases_to_disk()

    def find_databases(self, workspace_id: str) -> List[CodeQLDatabase]:
        """Find all databases for workspace."""
        return self._databases.get(workspace_id, [])

    def find_database(self, workspace_id: str, database_id: str) -> Optional[CodeQLDatabase]:
        """Find specific database."""
        databases = self._databases.get(workspace_id, [])
        for db in databases:
            if db.database_id == database_id:
                return db
        return None

