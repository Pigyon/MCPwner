"""List available tools."""

from config.tools import HEALTHY_TOOLS, TOOL_REGISTRY

# CodeQL and Linguist have bespoke wiring and are not in the registry, so they
# are listed explicitly; every other tool is derived from the registry so all
# categories (SAST, SCA, Secrets, Reconnaissance, Utilities, IaC) stay in sync
# automatically.
_BESPOKE_TOOLS = [t for t in ["codeql", "linguist"] if t in HEALTHY_TOOLS]

# Tools tracked in the README "Future Tools" roadmap, not yet wired.
_PLANNED_TOOLS = [
    "owasp-zap",
    "nikto",
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
