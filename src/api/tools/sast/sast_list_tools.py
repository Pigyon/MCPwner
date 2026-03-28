"""SAST tool discovery MCP tool."""

from typing import Optional

from config.languages import (
    BANDIT_LANGUAGES,
    BRAKEMAN_LANGUAGES,
    GOSEC_LANGUAGES,
    JOERN_LANGUAGES,
    NODEJSSCAN_LANGUAGES,
    PMD_LANGUAGES,
    PSALM_LANGUAGES,
    SEMGREP_LANGUAGES,
    YASA_LANGUAGES,
)
from deps import get_linguist_service

# Tool metadata with language support
SAST_TOOLS = {
    "semgrep": {
        "name": "Semgrep",
        "description": "Multi-language SAST tool for security and code quality",
        "languages": SEMGREP_LANGUAGES,
        "category": "sast",
    },
    "bandit": {
        "name": "Bandit",
        "description": "Python-specific security linter",
        "languages": BANDIT_LANGUAGES,
        "category": "sast",
    },
    "gosec": {
        "name": "Gosec",
        "description": "Go security checker",
        "languages": GOSEC_LANGUAGES,
        "category": "sast",
    },
    "brakeman": {
        "name": "Brakeman",
        "description": "Ruby on Rails security scanner",
        "languages": BRAKEMAN_LANGUAGES,
        "category": "sast",
    },
    "pmd": {
        "name": "PMD",
        "description": "Multi-language code analyzer",
        "languages": PMD_LANGUAGES,
        "category": "sast",
    },
    "psalm": {
        "name": "Psalm",
        "description": "PHP static analysis tool",
        "languages": PSALM_LANGUAGES,
        "category": "sast",
    },
    "nodejsscan": {
        "name": "NodeJsScan",
        "description": "Node.js/JavaScript SAST scanner for Express, Hapi, and other frameworks",
        "languages": NODEJSSCAN_LANGUAGES,
        "category": "sast",
    },
    "joern": {
        "name": "Joern",
        "description": "Code property graph based multi-language SAST platform for deep vulnerability analysis",
        "languages": JOERN_LANGUAGES,
        "category": "sast",
    },
    "yasa": {
        "name": "YASA",
        "description": "Multi-language SAST engine with UAST-based taint analysis for JavaScript/TypeScript, Java, Go, and Python",
        "languages": YASA_LANGUAGES,
        "category": "sast",
    },
}


def sast_list_tools(workspace_id: Optional[str] = None, show_all: bool = False) -> dict:
    """
    List available SAST tools with language compatibility.

    Args:
        workspace_id: Optional workspace ID to filter tools by detected languages
        show_all: If True, show all tools regardless of workspace languages

    Returns:
        Dictionary with available tools and their metadata
    """
    try:
        # If show_all or no workspace_id, return all tools
        if show_all or not workspace_id:
            return {"tools": SAST_TOOLS, "filtered": False}

        # Detect languages in workspace
        linguist_service = get_linguist_service()
        detected_languages = linguist_service.detect_languages(workspace_id, filter_codeql=False)

        # Filter tools by language compatibility
        compatible_tools = {}
        for tool_id, tool_info in SAST_TOOLS.items():
            tool_languages = set(tool_info["languages"])
            if tool_languages.intersection(detected_languages):
                compatible_tools[tool_id] = tool_info

        return {
            "workspace_id": workspace_id,
            "detected_languages": detected_languages,
            "tools": compatible_tools,
            "filtered": True,
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}
