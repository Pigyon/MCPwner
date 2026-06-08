"""Shared implementation for the per-category scan / report MCP tools.

SAST, SCA, Secrets and Reconnaissance all expose the same two operations —
"run a scan with tool X" and "get the latest report for tool X" — that differ
only by category. These helpers provide the single implementation; the
per-category modules keep thin, well-documented wrappers (their docstrings are
LLM-facing) that delegate here.
"""

import logging
from typing import Any, Dict, Optional

from config.tools import tools_for_category
from deps import get_service

logger = logging.getLogger(__name__)


def _unsupported(tool: str, supported: list) -> Dict[str, Any]:
    return {
        "status": "error",
        "error": f"Unsupported tool: {tool}",
        "supported_tools": supported,
    }


def run_scan(
    category: str,
    tool: str,
    workspace_id: str,
    scan_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run a scan for ``tool`` (which must belong to ``category``)."""
    supported = tools_for_category(category)
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
    if tool not in supported:
        return _unsupported(tool, supported)
    try:
        return get_service(tool).get_latest_report(workspace_id)
    except Exception as e:
        logger.error(f"Failed to get report for {tool}: {e}")
        return {"status": "error", "error": str(e)}
