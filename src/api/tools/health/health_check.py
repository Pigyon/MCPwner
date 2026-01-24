"""Health check tool."""

import os
from deps import get_codeql_service


def health_check() -> dict:
    """
    Check CodeQL availability and version.
    
    Returns:
        Dictionary with status and CodeQL version
    """
    try:
        service = get_codeql_service()
        version_info = service.get_version()
        
        return {
            "status": "healthy",
            "codeql_version": version_info.get("version", "unknown"),
            "transport": os.environ.get("MCP_TRANSPORT", "stdio")
        }
    except Exception:
        return {
            "status": "unavailable",
            "codeql_version": "unknown",
            "transport": os.environ.get("MCP_TRANSPORT", "stdio")
        }
