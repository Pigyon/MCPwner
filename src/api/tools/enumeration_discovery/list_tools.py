"""Enumeration & Discovery tool discovery MCP tool."""

from typing import Optional

ENUMERATION_DISCOVERY_TOOLS = {
    "subfinder": {
        "name": "Subfinder",
        "description": "Subdomain discovery tool",
        "category": "enumeration_discovery",
    },
    "amass": {
        "name": "Amass",
        "description": "Network mapping and attack surface discovery",
        "category": "enumeration_discovery",
    },
    "httpx": {
        "name": "httpx",
        "description": "HTTP toolkit for probing and analysis",
        "category": "enumeration_discovery",
    },
    "katana": {
        "name": "Katana",
        "description": "Web crawling framework for reconnaissance",
        "category": "enumeration_discovery",
    },
    "ffuf": {
        "name": "ffuf",
        "description": "Fast web fuzzer for content discovery",
        "category": "enumeration_discovery",
    },
    "nuclei": {
        "name": "Nuclei",
        "description": "Vulnerability scanner with template-based detection",
        "category": "enumeration_discovery",
    },
    "nmap": {
        "name": "Nmap",
        "description": "Network scanner for host and service discovery",
        "category": "enumeration_discovery",
    },
    "masscan": {
        "name": "Masscan",
        "description": "Fast port scanner for large-scale scanning",
        "category": "enumeration_discovery",
    },
    "arjun": {
        "name": "Arjun",
        "description": "HTTP parameter discovery tool",
        "category": "enumeration_discovery",
    },
    "gau": {
        "name": "gau",
        "description": "Get All URLs from web archives",
        "category": "enumeration_discovery",
    },
    "akto": {
        "name": "Akto",
        "description": "API security testing platform",
        "category": "enumeration_discovery",
    },
    "wafw00f": {
        "name": "wafw00f",
        "description": "Web Application Firewall detection tool",
        "category": "enumeration_discovery",
    },
    "gowitness": {
        "name": "Gowitness",
        "description": "Web screenshot utility for visual reconnaissance",
        "category": "enumeration_discovery",
    },
}


def enumeration_discovery_list_tools(workspace_id: Optional[str] = None, show_all: bool = False) -> dict:
    """
    List available Enumeration & Discovery tools.

    Args:
        workspace_id: Optional workspace ID (reserved for future filtering)
        show_all: If True, show all tools (default behavior for enumeration tools)

    Returns:
        Dictionary with available tools and their metadata
    """
    try:
        # Enumeration tools are not language-specific, so we always return all tools
        return {"tools": ENUMERATION_DISCOVERY_TOOLS, "filtered": False}

    except Exception as e:
        return {"status": "error", "error": str(e)}
