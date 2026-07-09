"""List available DAST tools."""

from typing import Optional

from api.tools.common import filter_tools_by_language, handle_tool_error

DAST_TOOLS = {
    "sqlmap": {
        "name": "SQLMap",
        "description": (
            "Automatic SQL injection detection and exploitation. Config: target, raw_request, data"
        ),
        "languages": [],
    },
    "nosqlmap": {
        "name": "NoSQLMap",
        "description": "NoSQL injection scanner for MongoDB and other NoSQL backends. Config: target",
        "languages": [],
    },
    "commix": {
        "name": "Commix",
        "description": "Command injection exploitation tool. Config: target, data",
        "languages": [],
    },
    "dalfox": {
        "name": "Dalfox",
        "description": (
            "Parameter-based XSS and open-redirect scanner with native JSON output. Config: target"
        ),
        "languages": [],
    },
    "sstimap": {
        "name": "SSTImap",
        "description": "Server-side template injection scanner. Config: target",
        "languages": [],
    },
    "ssrfmap": {
        "name": "SSRFmap",
        "description": "SSRF exploitation framework. Config: target, raw_request, param, module",
        "languages": [],
    },
    "jwt_tool": {
        "name": "jwt_tool",
        "description": "JWT vulnerability scanner. Config: target, token",
        "languages": [],
    },
    "interactsh-client": {
        "name": "Interactsh Client",
        "description": (
            "Out-of-band interaction client for blind vulnerability confirmation. "
            "Config: optional target"
        ),
        "languages": [],
    },
}


@handle_tool_error
def dast_list_tools(workspace_id: Optional[str] = None, show_all: bool = False) -> dict:
    """List available DAST security scanning tools."""
    return filter_tools_by_language("dast", DAST_TOOLS, workspace_id, show_all)
