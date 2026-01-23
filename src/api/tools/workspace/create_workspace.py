"""Create workspace tool."""

import sys
from fastmcp import tool
from workspace.manager import WorkspaceManager

workspace_manager = WorkspaceManager()


@tool()
def create_workspace(source_type: str, source: str) -> dict:
    """
    Create workspace from GitHub repo or local directory.
    
    Args:
        source_type: "github" or "local"
        source: GitHub URL or local directory path
        
    Returns:
        Dictionary with workspace_id, source_type, source, and created_at
    """
    print(f"[MCP SERVER] create_workspace called: type={source_type}, source={source}", file=sys.stderr)
    result = workspace_manager.create_workspace(source_type, source)
    print(f"[MCP SERVER] Workspace created: {result['workspace_id']}", file=sys.stderr)
    return result
