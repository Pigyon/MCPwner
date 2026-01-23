"""
Workspace Manager - Handles workspace lifecycle management.

This module provides the WorkspaceManager class for creating, listing,
retrieving, and deleting workspaces with UUID-based identification.
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime


class WorkspaceManager:
    """
    Manages workspace lifecycle including creation, listing, retrieval, and deletion.
    
    Workspaces are isolated analysis environments containing either cloned repositories
    or mounted local directories. Each workspace has a unique UUID4 identifier.
    """
    
    def __init__(self):
        """Initialize the WorkspaceManager with an empty workspace registry."""
        self._workspaces: Dict[str, Dict[str, Any]] = {}
    
    def create_workspace(
        self,
        source_type: str,
        source: str
    ) -> Dict[str, str]:
        """
        Create a new workspace with a unique UUID4 identifier.
        
        Args:
            source_type: Type of source ("github" or "local")
            source: GitHub URL or local directory path
            
        Returns:
            Dictionary containing:
                - workspace_id: Unique UUID4 identifier
                - source_type: Type of source
                - source: Source location
                - created_at: ISO 8601 timestamp
        """
        workspace_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"
        
        workspace_metadata = {
            "workspace_id": workspace_id,
            "source_type": source_type,
            "source": source,
            "created_at": created_at
        }
        
        self._workspaces[workspace_id] = workspace_metadata
        
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
            return True
        return False
