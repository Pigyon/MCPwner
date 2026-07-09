"""SAST tool discovery MCP tool."""

import logging
from typing import Optional

from api.tools.common import filter_tools_by_language, handle_tool_error
from config.languages import (
    BANDIT_LANGUAGES,
    BRAKEMAN_LANGUAGES,
    GOSEC_LANGUAGES,
    JOERN_LANGUAGES,
    NODEJSSCAN_LANGUAGES,
    OPENGREP_LANGUAGES,
    PMD_LANGUAGES,
    PSALM_LANGUAGES,
    SEMGREP_LANGUAGES,
    YASA_LANGUAGES,
)

logger = logging.getLogger(__name__)


SAST_TOOLS = {
    "semgrep": {
        "name": "Semgrep",
        "description": "Multi-language SAST tool for security and code quality",
        "languages": SEMGREP_LANGUAGES,
    },
    "bandit": {
        "name": "Bandit",
        "description": "Python-specific security linter",
        "languages": BANDIT_LANGUAGES,
    },
    "gosec": {
        "name": "Gosec",
        "description": "Go security checker",
        "languages": GOSEC_LANGUAGES,
    },
    "brakeman": {
        "name": "Brakeman",
        "description": "Ruby on Rails security scanner",
        "languages": BRAKEMAN_LANGUAGES,
    },
    "pmd": {
        "name": "PMD",
        "description": "Multi-language code analyzer",
        "languages": PMD_LANGUAGES,
    },
    "psalm": {
        "name": "Psalm",
        "description": "PHP static analysis tool",
        "languages": PSALM_LANGUAGES,
    },
    "nodejsscan": {
        "name": "NodeJsScan",
        "description": "Node.js/JavaScript SAST scanner for Express, Hapi, and other frameworks",
        "languages": NODEJSSCAN_LANGUAGES,
    },
    "joern": {
        "name": "Joern",
        "description": (
            "Code property graph based multi-language SAST platform for deep vulnerability analysis"
        ),
        "languages": JOERN_LANGUAGES,
    },
    "yasa": {
        "name": "YASA",
        "description": (
            "Multi-language SAST engine with UAST-based taint"
            " analysis for JavaScript/TypeScript, Java, Go, and Python"
        ),
        "languages": YASA_LANGUAGES,
    },
    "opengrep": {
        "name": "Opengrep",
        "description": (
            "Open-source multi-language SAST engine supporting 30+ languages with pattern-based analysis"
        ),
        "languages": OPENGREP_LANGUAGES,
    },
}


@handle_tool_error
def sast_list_tools(workspace_id: Optional[str] = None, show_all: bool = False) -> dict:
    """
    List available SAST tools with language compatibility.

    Args:
        workspace_id: Optional workspace ID to filter tools by detected languages
        show_all: If True, show all tools regardless of workspace languages

    Returns:
        Dictionary with available tools and their metadata
    """
    return filter_tools_by_language("sast", SAST_TOOLS, workspace_id, show_all)
