"""Workspace repository for data persistence."""

from typing import Dict, List, Optional
from models import Workspace, CodeQLDatabase


class WorkspaceRepository:
    """In-memory workspace repository."""
    
    def __init__(self):
        self._workspaces: Dict[str, Workspace] = {}
        self._databases: Dict[str, List[CodeQLDatabase]] = {}
    
    def save(self, workspace: Workspace) -> None:
        """Save workspace."""
        self._workspaces[workspace.workspace_id] = workspace
        if workspace.workspace_id not in self._databases:
            self._databases[workspace.workspace_id] = []
    
    def find_by_id(self, workspace_id: str) -> Optional[Workspace]:
        """Find workspace by ID."""
        return self._workspaces.get(workspace_id)
    
    def find_all(self) -> List[Workspace]:
        """Find all workspaces."""
        return list(self._workspaces.values())
    
    def delete(self, workspace_id: str) -> bool:
        """Delete workspace."""
        if workspace_id in self._workspaces:
            del self._workspaces[workspace_id]
            if workspace_id in self._databases:
                del self._databases[workspace_id]
            return True
        return False
    
    def save_database(self, database: CodeQLDatabase) -> None:
        """Save database metadata."""
        if database.workspace_id not in self._databases:
            self._databases[database.workspace_id] = []
        
        # Update existing or append new
        databases = self._databases[database.workspace_id]
        for i, db in enumerate(databases):
            if db.database_id == database.database_id:
                databases[i] = database
                return
        databases.append(database)
    
    def find_databases(self, workspace_id: str) -> List[CodeQLDatabase]:
        """Find all databases for workspace."""
        return self._databases.get(workspace_id, [])
    
    def find_database(
        self,
        workspace_id: str,
        database_id: str
    ) -> Optional[CodeQLDatabase]:
        """Find specific database."""
        databases = self._databases.get(workspace_id, [])
        for db in databases:
            if db.database_id == database_id:
                return db
        return None
