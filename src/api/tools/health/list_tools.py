"""List available tools."""

from config.tools import TOOL_REGISTRY

# CodeQL and Linguist have bespoke wiring and are not in the registry, so they
# are listed explicitly; every other tool is derived from the registry so all
# categories (SAST, SCA, Secrets, Reconnaissance, Utilities, IaC) stay in sync
# automatically.
_BESPOKE_TOOLS = ["codeql", "linguist"]

# Tools tracked in the README "Future Tools" roadmap (DAST), not yet wired.
_PLANNED_TOOLS = [
    "owasp-zap",
    "sqlmap",
    "nosqlmap",
    "dalfox",
    "nikto",
    "sstimap",
    "commix",
    "jwt_tool",
    "wapiti",
    "nuclei",
]


def health_list_tools() -> dict:
    """
    List available and planned security tools.

    Returns:
        Dictionary with available and planned tools
    """
    return {
        "available": _BESPOKE_TOOLS + list(TOOL_REGISTRY.keys()),
        "planned": _PLANNED_TOOLS,
    }
