"""SCA tool discovery MCP tool."""

import logging
from typing import Optional

from api.tools.common import filter_tools_by_language, handle_tool_error
from config.languages import (
    JAVASCRIPT_LANGUAGES,
)

logger = logging.getLogger(__name__)


SCA_TOOLS = {
    "osv-scanner": {
        "name": "OSV-Scanner",
        "description": "Vulnerability scanner using Google's distributed OSV database API",
        "languages": [],
    },
    "grype": {
        "name": "Grype",
        "description": "Vulnerability scanner for container images and filesystems",
        "languages": [],
    },
    "retirejs": {
        "name": "Retire.js",
        "description": "Detects the use of JavaScript libraries with known vulnerabilities",
        "languages": JAVASCRIPT_LANGUAGES,
    },
    "syft": {
        "name": "Syft",
        "description": "Generates a Software Bill of Materials (SBOM) from filesystems",
        "languages": [],
    },
}


@handle_tool_error
def sca_list_tools(workspace_id: Optional[str] = None, show_all: bool = False) -> dict:
    """
    List available SCA tools with language compatibility.

    Args:
        workspace_id: Optional workspace ID to filter tools by detected languages
        show_all: If True, show all tools regardless of workspace languages

    Returns:
        Dictionary with available tools and their metadata
    """
    return filter_tools_by_language("sca", SCA_TOOLS, workspace_id, show_all)
