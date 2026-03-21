"""Reconnaissance tool discovery MCP tool."""

from typing import Optional

RECONNAISSANCE_TOOLS = {
    "subfinder": {
        "name": "Subfinder",
        "description": "Subdomain discovery tool",
        "category": "reconnaissance",
    },
    "amass": {
        "name": "Amass",
        "description": "Network mapping and attack surface discovery",
        "category": "reconnaissance",
    },
    "httpx": {
        "name": "httpx",
        "description": "HTTP toolkit for probing and analysis",
        "category": "reconnaissance",
    },
    "katana": {
        "name": "Katana",
        "description": "Web crawling framework for reconnaissance",
        "category": "reconnaissance",
    },
    "ffuf": {
        "name": "ffuf",
        "description": "Fast web fuzzer for content discovery",
        "category": "reconnaissance",
    },
    "nuclei": {
        "name": "Nuclei",
        "description": "Vulnerability scanner with template-based detection",
        "category": "reconnaissance",
    },
    "nmap": {
        "name": "Nmap",
        "description": "Network scanner for host and service discovery",
        "category": "reconnaissance",
    },
    "masscan": {
        "name": "Masscan",
        "description": "Fast port scanner for large-scale scanning",
        "category": "reconnaissance",
    },
    "arjun": {
        "name": "Arjun",
        "description": "HTTP parameter discovery tool",
        "category": "reconnaissance",
    },
    "gau": {
        "name": "gau",
        "description": "Get All URLs from web archives",
        "category": "reconnaissance",
    },
    "akto": {
        "name": "Akto",
        "description": "API security testing platform",
        "category": "reconnaissance",
    },
    "wafw00f": {
        "name": "wafw00f",
        "description": "Web Application Firewall detection tool",
        "category": "reconnaissance",
    },
    "gowitness": {
        "name": "Gowitness",
        "description": "Web screenshot utility for visual reconnaissance",
        "category": "reconnaissance",
    },
}


def reconnaissance_list_tools(workspace_id: Optional[str] = None, show_all: bool = False) -> dict:
    """
    List available Reconnaissance tools.

    Args:
        workspace_id: Optional workspace ID (reserved for future filtering)
        show_all: If True, show all tools (default behavior for reconnaissance tools)

    Returns:
        Dictionary with available tools and their metadata
    """
    try:
        # Reconnaissance tools are not language-specific, so we always return all tools
        return {"tools": RECONNAISSANCE_TOOLS, "filtered": False}

    except Exception as e:
        return {"status": "error", "error": str(e)}
