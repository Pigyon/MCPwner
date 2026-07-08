"""List available DAST tools."""

DAST_TOOLS = {
    "sqlmap": {
        "name": "SQLMap",
        "description": (
            "Automatic SQL injection detection and exploitation. Config: target, raw_request, data"
        ),
        "languages": [],
        "category": "dast",
    },
    "nosqlmap": {
        "name": "NoSQLMap",
        "description": "NoSQL injection scanner for MongoDB and other NoSQL backends. Config: target",
        "languages": [],
        "category": "dast",
    },
    "commix": {
        "name": "Commix",
        "description": "Command injection exploitation tool. Config: target, data",
        "languages": [],
        "category": "dast",
    },
    "dalfox": {
        "name": "Dalfox",
        "description": (
            "Parameter-based XSS and open-redirect scanner with native JSON output. Config: target"
        ),
        "languages": [],
        "category": "dast",
    },
    "sstimap": {
        "name": "SSTImap",
        "description": "Server-side template injection scanner. Config: target",
        "languages": [],
        "category": "dast",
    },
    "ssrfmap": {
        "name": "SSRFmap",
        "description": "SSRF exploitation framework. Config: target, raw_request, param, module",
        "languages": [],
        "category": "dast",
    },
    "jwt_tool": {
        "name": "jwt_tool",
        "description": "JWT vulnerability scanner. Config: target, token",
        "languages": [],
        "category": "dast",
    },
    "interactsh-client": {
        "name": "Interactsh Client",
        "description": (
            "Out-of-band interaction client for blind vulnerability confirmation. "
            "Config: optional target"
        ),
        "languages": [],
        "category": "dast",
    },
}


def dast_list_tools() -> dict:
    """List available DAST security scanning tools."""
    return {"tools": DAST_TOOLS, "filtered": False}
