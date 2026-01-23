#!/usr/bin/env python3
"""
Enhanced MCP server with robust multi-transport support.
Supports STDIO, SSE, and future WebSocket transports.
"""

from fastmcp import FastMCP
from typing import Dict, List, Any
import sys
import os
from config import load_config, ConfigError
from workspace.manager import WorkspaceManager
from tools.codeql_manager import CodeQLManager

# Load configuration on startup
try:
    config = load_config()
    print(f"Configuration loaded successfully from config.yaml", file=sys.stderr)
except ConfigError as e:
    print(f"Configuration error: {e}", file=sys.stderr)
    sys.exit(1)

# Initialize FastMCP server
mcp = FastMCP("MCPwner")

# Initialize managers
workspace_manager = WorkspaceManager()
codeql_manager = CodeQLManager()


# ============================================================================
# MCP TOOLS - These work across ALL transports
# ============================================================================

@mcp.tool()
def health_check() -> Dict[str, str]:
    """
    Check CodeQL availability and version.
    
    Returns:
        Dictionary with status and CodeQL version
    """
    is_available = codeql_manager.check_availability()
    version = codeql_manager.get_version() if is_available else None
    
    return {
        "status": "healthy" if is_available else "unavailable",
        "codeql_version": version or "unknown",
        "transport": os.environ.get("MCP_TRANSPORT", "stdio")
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
    print(f"[MCP SERVER] create_workspace called: type={source_type}, source={source}", file=sys.stderr)
    result = workspace_manager.create_workspace(source_type, source)
    print(f"[MCP SERVER] Workspace created: {result['workspace_id']}", file=sys.stderr)
    return result


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
def detect_languages(workspace_id: str) -> Dict[str, Any]:
    """
    Detect programming languages in a workspace.
    
    Args:
        workspace_id: UUID of the workspace
        
    Returns:
        Dictionary with detected languages list
    """
    try:
        workspace = workspace_manager.get_workspace(workspace_id)
        if not workspace:
            return {
                "status": "error",
                "error": f"Workspace not found: {workspace_id}"
            }
        
        workspace_path = workspace.get("path")
        if not workspace_path:
            return {
                "status": "error",
                "error": "Workspace path not found"
            }
        
        languages = codeql_manager.detect_languages(workspace_path)
        
        return {
            "workspace_id": workspace_id,
            "languages": languages,
            "count": len(languages)
        }
        
    except Exception as e:
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
    try:
        workspace = workspace_manager.get_workspace(workspace_id)
        if not workspace:
            return {
                "status": "error",
                "error": f"Workspace not found: {workspace_id}"
            }
        
        workspace_path = workspace.get("path")
        if not workspace_path:
            return {
                "status": "error",
                "error": "Workspace path not found"
            }
        
        if not language:
            detected_languages = codeql_manager.detect_languages(workspace_path)
            if not detected_languages:
                return {
                    "status": "error",
                    "error": "No supported languages detected in workspace"
                }
            language = detected_languages[0]
        
        db_metadata = codeql_manager.create_database(
            workspace_id=workspace_id,
            language=language,
            workspace_path=workspace_path
        )
        
        workspace_manager.add_database(workspace_id, db_metadata)
        
        return {
            "database_id": db_metadata["database_id"],
            "language": db_metadata["language"],
            "status": "created",
            "created_at": db_metadata["created_at"]
        }
        
    except ValueError as e:
        return {
            "status": "error",
            "error": str(e)
        }
    except RuntimeError as e:
        return {
            "status": "error",
            "error": str(e)
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
    try:
        return workspace_manager.list_databases(workspace_id)
    except ValueError as e:
        return [{
            "status": "error",
            "error": str(e)
        }]


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


# ============================================================================
# TRANSPORT CONFIGURATION
# ============================================================================

def get_transport_config():
    """Determine transport configuration from environment and config file."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    
    config_data = {
        "transport": transport,
        "host": "0.0.0.0",
        "port": 13370
    }
    
    # Load from config file if available
    if transport == "sse":
        server_config = config.get("server", {})
        config_data["host"] = server_config.get("host", "0.0.0.0")
        config_data["port"] = server_config.get("port", 13370)
    
    return config_data


def run_server():
    """Run the MCP server with appropriate transport."""
    transport_config = get_transport_config()
    transport = transport_config["transport"]
    
    print(f"Starting MCPwner MCP server...", file=sys.stderr)
    print(f"Transport: {transport}", file=sys.stderr)
    
    if transport == "sse":
        host = transport_config["host"]
        port = transport_config["port"]
        print(f"SSE endpoint: http://{host}:{port}/sse", file=sys.stderr)
        print(f"Health check: http://{host}:{port}/health", file=sys.stderr)
        
        # Run with SSE transport
        mcp.run(transport="sse", host=host, port=port)
        
    elif transport == "stdio":
        print(f"STDIO mode: Reading from stdin, writing to stdout", file=sys.stderr)
        print(f"Compatible with: Claude Desktop, MCP CLI tools", file=sys.stderr)
        
        # Run with STDIO transport (default)
        mcp.run()
        
    else:
        print(f"ERROR: Unknown transport '{transport}'", file=sys.stderr)
        print(f"Supported transports: stdio, sse", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
