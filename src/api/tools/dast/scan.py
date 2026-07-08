"""Generic DAST scan tool."""

import logging
from typing import Any, Dict, Optional

from config.tools import resolve_tool_name, tools_for_category
from deps import get_service, get_workspace_service

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = tools_for_category("dast")
AUTO_WORKSPACE = "auto"


def run_dast_scan(
    tool: str,
    target: Optional[str] = None,
    workspace_id: Optional[str] = None,
    scan_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute a DAST scan using the specified tool.

    Args:
        tool: DAST tool name (sqlmap, nosqlmap, commix, dalfox, sstimap,
              ssrfmap, jwt_tool, interactsh-client).
        target: URL to scan (required for most tools).
        workspace_id: Workspace UUID. Use "auto" or omit to create a virtual workspace.
        scan_path: Optional relative path within workspace.
        config: Tool-specific options. Common keys:
            - raw_request: Raw HTTP request text (sqlmap, ssrfmap)
            - data: POST body data (commix, sqlmap)
            - token: JWT token (jwt_tool)
            - param: Parameter name (ssrfmap)
            - module: SSRFmap module name (ssrfmap)
            - timeout_seconds: Scan timeout override
    """
    tool = resolve_tool_name(tool)

    if target:
        config = {**(config or {}), "target": target}
    elif config and config.get("target"):
        target = config["target"]
    elif tool != "interactsh-client":
        return {
            "status": "error",
            "error": "A 'target' is required for DAST scans (e.g. target='https://example.com/page').",
        }

    if tool not in SUPPORTED_TOOLS:
        return {
            "status": "error",
            "error": f"Unsupported tool: {tool}",
            "supported_tools": SUPPORTED_TOOLS,
        }

    try:
        if not workspace_id or workspace_id == AUTO_WORKSPACE:
            logger.info("Creating virtual workspace for DAST scan")
            workspace_service = get_workspace_service()
            workspace_result = workspace_service.create_workspace(
                source_type="virtual", source=f"dast-{tool}"
            )
            workspace_id = workspace_result["workspace_id"]

        service = get_service(tool)
        result = service.scan(workspace_id, scan_path, config)
        if "workspace_id" not in result:
            result["workspace_id"] = workspace_id
        return result
    except Exception as exc:
        logger.error("DAST scan failed for %s: %s", tool, exc)
        return {"status": "error", "error": str(exc)}
