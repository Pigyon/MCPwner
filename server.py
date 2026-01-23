from fastmcp import FastMCP
from typing import Dict, List, Any
import uuid
import sys
from config import load_config, ConfigError
from workspace.manager import WorkspaceManager

# Load configuration on startup
try:
    config = load_config()
    print(f"Configuration loaded successfully from config.yaml", file=sys.stderr)
except ConfigError as e:
    print(f"Configuration error: {e}", file=sys.stderr)
    sys.exit(1)

# Initialize FastMCP server
mcp = FastMCP("MCPwner")

# Initialize WorkspaceManager
workspace_manager = WorkspaceManager()


@mcp.tool()
def health_check() -> Dict[str, str]:
    """
    Check CodeQL availability and version.
    
    Returns:
        Dictionary with status and CodeQL version
    """
    return {
        "status": "healthy",
        "codeql_version": "mock"
    }


@mcp.tool()
def create_workspace(source_type: str, source: str) -> Dict[str, str]:
    """
    Create workspace from GitHub repo or local directory.
    
    Args:
        source_type: "github" or "local"
        source: GitHub URL or local directory path
        
    Returns:
        Dictionary with workspace_id, source_type, source, and created_at
    """
    return workspace_manager.create_workspace(source_type, source)


@mcp.tool()
def list_workspaces() -> List[Dict[str, Any]]:
    """
    List all active workspaces.
    
    Returns:
        Array of workspace metadata
    """
    return workspace_manager.list_workspaces()


@mcp.tool()
def cleanup_workspace(workspace_id: str) -> Dict[str, str]:
    """
    Manually cleanup a workspace.
    
    Args:
        workspace_id: UUID of the workspace to clean up
        
    Returns:
        Dictionary with cleanup status
    """
    try:
        return workspace_manager.cleanup_workspace(workspace_id)
    except ValueError as e:
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def create_codeql_database(workspace_id: str, language: str = None) -> Dict[str, str]:
    """
    Create CodeQL database for workspace.
    
    Args:
        workspace_id: UUID of the workspace
        language: Optional language (auto-detect if not provided)
        
    Returns:
        Dictionary with database_id, language, and status
    """
    return {
        "database_id": "mock-db",
        "language": language or "python",
        "status": "created"
    }


@mcp.tool()
def list_databases(workspace_id: str) -> List[Dict[str, Any]]:
    """
    List databases for a workspace.
    
    Args:
        workspace_id: UUID of the workspace
        
    Returns:
        Array of database metadata
    """
    return []


@mcp.tool()
def execute_query(
    workspace_id: str,
    database_id: str,
    query_type: str,
    query: str
) -> Dict[str, Any]:
    """
    Execute CodeQL query on database.
    
    Args:
        workspace_id: UUID of the workspace
        database_id: UUID of the database
        query_type: "builtin" or "custom"
        query: Query pack name or custom query code
        
    Returns:
        Structured vulnerability results
    """
    return {
        "results": [],
        "message": "mock execution"
    }


@mcp.tool()
def list_query_packs(language: str = None) -> List[str]:
    """
    List available CodeQL query packs by language.
    
    Args:
        language: Optional language filter
        
    Returns:
        Array of query pack names
    """
    return ["security-extended", "security-and-quality"]


@mcp.tool()
def list_tools() -> Dict[str, List[str]]:
    """
    List available and planned security tools.
    
    Returns:
        Dictionary with available and planned tools
    """
    return {
        "available": ["codeql"],
        "planned": ["semgrep", "owasp-zap"]
    }


if __name__ == "__main__":
    # Run the MCP server with stdio transport
    mcp.run()
