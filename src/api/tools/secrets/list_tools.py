"""List available Secrets tools."""

from config.tools import tools_for_category

# Tool metadata, mirroring the shape returned by the SAST/SCA list_tools tools.
# Secrets scanners are language-agnostic, so there is nothing to filter on.
SECRETS_TOOLS = {
    "gitleaks": {
        "name": "Gitleaks",
        "description": "Fast secret scanner for git repos and files",
        "languages": [],
        "category": "secrets",
    },
    "trufflehog": {
        "name": "TruffleHog",
        "description": "Finds and verifies leaked credentials across many detectors",
        "languages": [],
        "category": "secrets",
    },
    "whispers": {
        "name": "Whispers",
        "description": "Static structured-text secret detector (configs, code, env files)",
        "languages": [],
        "category": "secrets",
    },
    "detect-secrets": {
        "name": "detect-secrets",
        "description": "Entropy- and pattern-based secret detection with baselining",
        "languages": [],
        "category": "secrets",
    },
    "hawk-scanner": {
        "name": "Hawk-Eye",
        "description": "Scans data stores and filesystems for PII and secrets",
        "languages": [],
        "category": "secrets",
    },
}


def secrets_list_tools() -> dict:
    """
    List available Secrets scanning tools.

    Returns:
        Dictionary with available tools and their metadata
    """
    healthy = set(tools_for_category("secrets"))
    available_tools = {k: v for k, v in SECRETS_TOOLS.items() if k in healthy}
    return {"tools": available_tools, "filtered": True}
