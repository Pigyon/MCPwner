"""Shared implementation for the per-category scan / report MCP tools.

SAST, SCA, Secrets and Reconnaissance all expose the same two operations —
"run a scan with tool X" and "get the latest report for tool X" — that differ
only by category. These helpers provide the single implementation; the
per-category modules keep thin, well-documented wrappers (their docstrings are
LLM-facing) that delegate here.
"""

import logging
from functools import wraps
from typing import Any, Dict, Optional

from config.tools import resolve_tool_name, tools_for_category
from deps import get_linguist_service, get_service

logger = logging.getLogger(__name__)


def handle_tool_error(func):
    """Decorator to catch and format exceptions for tool endpoints."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            return {"status": "error", "error": str(e)}

    return wrapper


def filter_tools_by_language(
    category: str,
    all_tools_dict: Dict[str, Any],
    workspace_id: Optional[str] = None,
    show_all: bool = False,
) -> Dict[str, Any]:
    """
    Filter tools for a category by workspace languages.
    """
    healthy = set(tools_for_category(category))
    available_tools = {}
    for k, v in all_tools_dict.items():
        if k in healthy:
            tool_info = v.copy()
            tool_info.pop("category", None)
            available_tools[k] = tool_info

    if show_all or not workspace_id:
        return {"tools": available_tools, "filtered": False}

    try:
        linguist_service = get_linguist_service()
        detected_languages = linguist_service.detect_languages(workspace_id, filter_codeql=False)

        compatible_tools = {}
        for tool_id, tool_info in available_tools.items():
            tool_languages = tool_info.get("languages", [])
            if not tool_languages:
                compatible_tools[tool_id] = tool_info
                continue

            tool_languages_set = set(tool_languages)
            if tool_languages_set.intersection(detected_languages):
                compatible_tools[tool_id] = tool_info

        return {
            "workspace_id": workspace_id,
            "detected_languages": list(detected_languages),
            "tools": compatible_tools,
            "filtered": True,
        }
    except Exception as e:
        logger.warning(
            f"Linguist language detection failed: {e}. "
            f"Gracefully returning all healthy {category.upper()} tools."
        )
        return {
            "tools": available_tools,
            "filtered": False,
            "note": f"Language detection unavailable: {e}",
        }


# Tools that are commonly requested through the generic scan endpoints but are
# wired separately. Map them to an actionable hint instead of a bare "unsupported".
_SPECIAL_TOOL_HINTS = {
    "codeql": (
        "CodeQL is not run via run_sast_scan. Use the dedicated CodeQL tools: "
        "create_codeql_database, then execute_query "
        "(see list_query_packs and list_databases)."
    ),
    "linguist": (
        "Linguist is not a scan tool. Use detect_languages to identify a workspace's languages."
    ),
}


def _unsupported(tool: str, supported: list) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "status": "error",
        "error": f"Unsupported tool: {tool}",
        "supported_tools": supported,
    }
    hint = _SPECIAL_TOOL_HINTS.get((tool or "").lower().strip())
    if hint:
        result["hint"] = hint
    return result


def run_scan(
    category: str,
    tool: str,
    workspace_id: str,
    scan_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run a scan for ``tool`` (which must belong to ``category``)."""
    supported = tools_for_category(category)
    tool = resolve_tool_name(tool)
    if tool not in supported:
        return _unsupported(tool, supported)
    try:
        return get_service(tool).scan(workspace_id, scan_path, config)
    except Exception as e:
        logger.error(f"Scan failed for {tool}: {e}")
        return {"status": "error", "error": str(e)}


def get_report(category: str, tool: str, workspace_id: str) -> Dict[str, Any]:
    """Get the latest report for ``tool`` (which must belong to ``category``)."""
    supported = tools_for_category(category)
    tool = resolve_tool_name(tool)
    if tool not in supported:
        return _unsupported(tool, supported)
    try:
        return get_service(tool).get_latest_report(workspace_id)
    except Exception as e:
        logger.error(f"Failed to get report for {tool}: {e}")
        return {"status": "error", "error": str(e)}


def create_scan_tool(category: str):
    """Factory to create a scan tool function for FastMCP."""
    if category in ("dast", "utilities", "reconnaissance"):
        # Custom scan tools that take target, auto-create workspaces, and have custom target validation
        def scan_tool(
            tool: str,
            target: Optional[str] = None,
            workspace_id: Optional[str] = None,
            scan_path: Optional[str] = None,
            config: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            from deps import get_workspace_service

            tool = resolve_tool_name(tool)
            supported = tools_for_category(category)
            if tool not in supported:
                return _unsupported(tool, supported)

            # Target validation
            chainable_tools = ["httpx", "katana", "arjun", "gau", "wafw00f", "kiterunner", "ffuf"]
            is_chained = (
                category == "reconnaissance"
                and config
                and config.get("source_tool")
                and tool in chainable_tools
            )

            if target:
                config = {**(config or {}), "target": target}
            elif config and config.get("target"):
                target = config["target"]
            elif is_chained:
                pass
            elif not (category == "dast" and tool == "interactsh-client"):
                # Missing target
                expected_format = (
                    "example.com" if category == "reconnaissance" else "https://example.com/page"
                )
                return {
                    "status": "error",
                    "error": (
                        f"A 'target' is required for {category.upper()} scans "
                        f"(e.g. target='{expected_format}')."
                    ),
                }

            try:
                if not workspace_id or workspace_id == "auto":
                    logger.info(f"Creating virtual workspace for {category} scan")
                    workspace_service = get_workspace_service()
                    workspace_result = workspace_service.create_workspace(
                        source_type="virtual", source=f"{category}-{tool}"
                    )
                    workspace_id = workspace_result["workspace_id"]

                result = get_service(tool).scan(workspace_id, scan_path, config)
                if isinstance(result, dict) and "workspace_id" not in result:
                    result["workspace_id"] = workspace_id
                return result
            except Exception as e:
                logger.error(f"{category.upper()} scan failed for {tool}: {e}")
                return {"status": "error", "error": str(e)}

        scan_tool.__name__ = f"run_{category}_scan"
        scan_tool.__doc__ = f"""Execute a {category.upper()} scan using the specified tool.

Args:
    tool: Name of the {category.upper()} tool to run
    target: Target to scan (URL, domain, IP, etc.)
    workspace_id: Workspace UUID. Use "auto" or omit to create a virtual workspace
    scan_path: Optional relative path within workspace to scan
    config: Optional tool-specific configuration
"""
        return scan_tool

    # Generic scan tool
    def scan_tool(
        tool: str,
        workspace_id: str,
        scan_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return run_scan(category, tool, workspace_id, scan_path, config)

    scan_tool.__name__ = f"run_{category}_scan"
    scan_tool.__doc__ = f"""Execute a {category.upper()} scan using the specified tool.

Args:
    tool: Name of the {category.upper()} tool to run
    workspace_id: UUID of the workspace
    scan_path: Optional relative path within workspace to scan
    config: Optional tool-specific configuration
"""
    return scan_tool


def create_report_tool(category: str):
    """Factory to create a generic report retrieval tool function for FastMCP."""

    def report_tool(tool: str, workspace_id: str) -> Dict[str, Any]:
        return get_report(category, tool, workspace_id)

    report_tool.__name__ = f"get_{category}_report"
    report_tool.__doc__ = f"Get the latest {category.upper()} scan report for the specified tool."
    return report_tool
