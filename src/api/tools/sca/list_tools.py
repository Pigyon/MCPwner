import logging
from typing import Optional

from config.languages import (
    JAVASCRIPT_LANGUAGES,
)
from config.tools import tools_for_category
from deps import get_linguist_service

"""SCA tool discovery MCP tool."""


logger = logging.getLogger(__name__)


# Tool metadata with language support
# If languages is empty, it means the tool supports all languages or is language-agnostic
SCA_TOOLS = {
    "osv-scanner": {
        "name": "OSV-Scanner",
        "description": "Vulnerability scanner using Google's distributed OSV database API",
        "languages": [],  # Supports multiple languages via lockfiles
        "category": "sca",
    },
    "grype": {
        "name": "Grype",
        "description": "Vulnerability scanner for container images and filesystems",
        "languages": [],  # Language agnostic (scans filesystem/images)
        "category": "sca",
    },
    "retirejs": {
        "name": "Retire.js",
        "description": "Detects the use of JavaScript libraries with known vulnerabilities",
        "languages": JAVASCRIPT_LANGUAGES,
        "category": "sca",
    },
    "syft": {
        "name": "Syft",
        "description": "Generates a Software Bill of Materials (SBOM) from filesystems",
        "languages": [],  # Language agnostic
        "category": "sca",
    },
}


def sca_list_tools(workspace_id: Optional[str] = None, show_all: bool = False) -> dict:
    """
    List available SCA tools with language compatibility.

    Args:
        workspace_id: Optional workspace ID to filter tools by detected languages
        show_all: If True, show all tools regardless of workspace languages

    Returns:
        Dictionary with available tools and their metadata
    """
    try:
        # Filter available tools based on health
        healthy = set(tools_for_category("sca"))
        available_tools = {k: v for k, v in SCA_TOOLS.items() if k in healthy}

        # If show_all or no workspace_id, return all tools
        if show_all or not workspace_id:
            return {"tools": available_tools, "filtered": False}

        # Detect languages in workspace
        try:
            linguist_service = get_linguist_service()
            detected_languages = linguist_service.detect_languages(workspace_id, filter_codeql=False)

            # Filter tools by language compatibility
            compatible_tools = {}
            for tool_id, tool_info in available_tools.items():
                tool_languages = tool_info["languages"]

                # If tool has no specific language requirements (empty list), it's compatible
                if not tool_languages:
                    compatible_tools[tool_id] = tool_info
                    continue

                tool_languages_set = set(tool_languages)
                if tool_languages_set.intersection(detected_languages):
                    compatible_tools[tool_id] = tool_info

            return {
                "workspace_id": workspace_id,
                "detected_languages": detected_languages,
                "tools": compatible_tools,
                "filtered": True,
            }
        except Exception as e:
            logger.warning(
                f"Linguist language detection failed: {e}. Gracefully returning all healthy SCA tools."
            )
            return {
                "tools": available_tools,
                "filtered": False,
                "note": f"Language detection unavailable: {e}",
            }

    except Exception as e:
        return {"status": "error", "error": str(e)}
