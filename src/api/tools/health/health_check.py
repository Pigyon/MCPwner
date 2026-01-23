"""Health check tool."""

import os
from fastmcp import tool
from tools.codeql_manager import CodeQLManager

codeql_manager = CodeQLManager()


@tool()
def health_check() -> dict:
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
