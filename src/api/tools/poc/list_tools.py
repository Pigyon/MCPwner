"""PoC sandbox tool discovery MCP tool."""

from typing import Optional

from api.tools.common import filter_tools_by_language, handle_tool_error

POC_TOOLS = {
    "poc-sandbox": {
        "name": "PoC-Script Sandbox",
        "description": (
            "Runs an agent-authored, multi-step exploit script (stateful login -> act -> "
            "assert) against a target and returns a DETERMINISTIC oracle verdict. Use this "
            "to PROVE the vulnerability classes off-the-shelf DAST cannot: IDOR/BOLA "
            "(two-account differential), broken access control (low-priv call to a privileged "
            "endpoint), race/TOCTOU (concurrent requests), and multi-step business-logic / "
            "workflow bypass. The script proves success by exiting 0 (or printing "
            "MCPWNER_ORACLE_PASS) and failure by exiting non-zero (or MCPWNER_ORACLE_FAIL); "
            "structured evidence goes on a MCPWNER_ORACLE_JSON:{...} line. A timed-out script "
            "never passes. Config: script (required source string), interpreter "
            "('python' default | 'bash'), target (optional, exposed as $TARGET and argv[1]), "
            "env (dict of extra env vars, e.g. captured session cookies/tokens), files "
            "(dict {relpath: contents} of auxiliary files), args (extra CLI args), "
            "timeout (seconds, default 120, max 600)."
        ),
        "languages": [],
    },
}


@handle_tool_error
def poc_list_tools(workspace_id: Optional[str] = None, show_all: bool = False) -> dict:
    """List available PoC validation tools (deterministic-oracle exploit runners)."""
    return filter_tools_by_language("poc", POC_TOOLS, workspace_id, show_all)
