"""List available Secrets tools."""

from api.tools.common import filter_tools_by_language, handle_tool_error

SECRETS_TOOLS = {
    "gitleaks": {
        "name": "Gitleaks",
        "description": "Fast secret scanner for git repos and files",
        "languages": [],
    },
    "trufflehog": {
        "name": "TruffleHog",
        "description": "Finds and verifies leaked credentials across many detectors",
        "languages": [],
    },
    "whispers": {
        "name": "Whispers",
        "description": "Static structured-text secret detector (configs, code, env files)",
        "languages": [],
    },
    "detect-secrets": {
        "name": "detect-secrets",
        "description": "Entropy- and pattern-based secret detection with baselining",
        "languages": [],
    },
    "hawk-scanner": {
        "name": "Hawk-Eye",
        "description": "Scans data stores and filesystems for PII and secrets",
        "languages": [],
    },
}


@handle_tool_error
def secrets_list_tools() -> dict:
    """
    List available Secrets scanning tools.

    Returns:
        Dictionary with available tools and their metadata
    """
    res = filter_tools_by_language("secrets", SECRETS_TOOLS, None, True)
    res["filtered"] = True
    return res
