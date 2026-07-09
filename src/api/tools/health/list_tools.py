"""List available tools."""

from api.tools.common import handle_tool_error
from config.tools import TOOL_REGISTRY, get_bespoke_tools

# CodeQL and Linguist have bespoke wiring and are not in the registry, so they
# are listed explicitly; every other tool is derived from the registry so all
# categories (SAST, SCA, Secrets, Reconnaissance, Utilities, IaC) stay in sync
# automatically.

# Tools tracked in the README "Future Tools" roadmap, not yet wired.
_PLANNED_TOOLS = [
    "owasp-zap",
    "nikto",
    "wapiti",
    "nuclei",
]


@handle_tool_error
def health_list_tools() -> dict:
    """
    List available and planned security tools.

    Returns:
        Dictionary with available and planned tools
    """
    return {
        "available": get_bespoke_tools() + list(TOOL_REGISTRY.keys()),
        "planned": _PLANNED_TOOLS,
    }
