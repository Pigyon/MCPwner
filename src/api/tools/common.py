"""Shared implementation for the per-category scan / report MCP tools.

SAST, SCA, Secrets and Reconnaissance all expose the same two operations —
"run a scan with tool X" and "get the latest report for tool X" — that differ
only by category. These helpers provide the single implementation; the
per-category modules keep thin, well-documented wrappers (their docstrings are
LLM-facing) that delegate here.
"""

import logging
from typing import Any, Dict, Optional

from config.tools import resolve_tool_name, tools_for_category
from deps import get_service

logger = logging.getLogger(__name__)


# Tools that are commonly requested through the generic scan endpoints but are
# wired separately. Map them to an actionable hint instead of a bare "unsupported".
_SPECIAL_TOOL_HINTS = {
    "codeql": (
        "CodeQL is not run via run_sast_scan. Use the dedicated CodeQL tools: "
        "create_codeql_database, then execute_query "
        "(see list_query_packs and list_databases)."
    ),
    "linguist": (
        "Linguist is not a scan tool. Use detect_languages to identify a "
        "workspace's languages."
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
