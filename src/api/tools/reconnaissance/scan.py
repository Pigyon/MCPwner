"""Generic Reconnaissance scan tool."""

import logging
from typing import Any, Dict, List, Optional

from deps import (
    get_amass_service,
    get_arjun_service,
    get_bbot_service,
    get_ffuf_service,
    get_gau_service,
    get_httpx_service,
    get_katana_service,
    get_kiterunner_service,
    get_masscan_service,
    get_nmap_service,
    get_subfinder_service,
    get_wafw00f_service,
    get_workspace_service,
)

logger = logging.getLogger(__name__)


SUPPORTED_TOOLS = [
    "subfinder",
    "amass",
    "httpx",
    "katana",
    "ffuf",
    "nmap",
    "masscan",
    "bbot",
    "arjun",
    "gau",
    "wafw00f",
    "kiterunner",
]

# Tools that support source_tool chaining (target is optional when source_tool is set)
CHAINABLE_TOOLS = [
    "httpx",
    "katana",
    "arjun",
    "gau",
    "wafw00f",
    "kiterunner",
    "ffuf",
]


def run_reconnaissance_scan(
    tool: str,
    target: Optional[str] = None,
    workspace_id: Optional[str] = None,
    scan_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute a Reconnaissance scan using the specified tool.

    Args:
        tool: Name of the reconnaissance tool to run.
              Supported: subfinder, amass, httpx, katana, ffuf, nmap, masscan, bbot,
                         arjun, gau, wafw00f, kiterunner.
        target: The domain, IP, URL, or CIDR to scan (e.g. "example.com").
                Required unless config.source_tool is set (for chained scans).
        workspace_id: UUID of the workspace (optional - auto-creates if not provided).
                      IMPORTANT: reuse the same workspace_id across chained scans to keep
                      all reports together.
        scan_path: Optional relative path within workspace to scan.
        config: Optional tool-specific configuration dict for advanced options.

            CHAINING — pass results from one tool to the next automatically:
              Set source_tool to the name of a previously run tool in the same workspace.
              The tool will auto-read targets from that tool's latest report.
              Example: config={"source_tool": "httpx"} — reads URLs from httpx report.
              When source_tool is set, 'target' is optional (can still be combined).

              Supported source_tool values per tool:
                httpx:      subfinder, amass, bbot, nmap, masscan, ffuf
                katana:     httpx, subfinder, amass, bbot, nmap, masscan, ffuf, gau
                arjun:      httpx, katana, gau, ffuf, bbot
                gau:        subfinder, amass, bbot, httpx
                wafw00f:    httpx, subfinder, amass, bbot, katana
                kiterunner: httpx, katana, gau, subfinder, amass, bbot
                ffuf:       httpx, katana, gau (extracts base URL for fuzzing)

            BBOT config (the scan response includes a structured summary with suggested_next_steps):
              preset: preset name(s), comma-separated. Default: 'subdomain-enum'.
                  Quick:  'subdomain-enum' (51 modules, fast)
                  Web:    'web-basic' (18 modules) or 'web-thorough' (32 modules, aggressive)
                  Combo:  'subdomain-enum,web-basic' or 'subdomain-enum,web-thorough'
                  Vuln:   'nuclei' or 'nuclei-intense'
                  Full:   'deep' (stacks 8 presets + aggressive, very slow)
              flags: 'passive', 'safe', or 'aggressive'
              modules: space-separated e.g. 'httpx sslcert portscan'
              strict_scope: bool, fast_mode: bool, allow_deadly: bool

            AMASS config:
              passive: bool (default: false) — passive-only enumeration, faster but fewer results
              timeout: int — scan timeout in minutes (default: 30)

            MASSCAN config:
              rate: int — packets per second (default: 100, max: 10000)
              ports: str — port range (default: "1-1000")

            NMAP config:
              timeout: int — per-host timeout in seconds (default: 300)
              ports: str — port range (default: "1-1000")

    Returns:
        Scan results with workspace_id, finding_count, and tool-specific summary.
    """
    # Resolve target from either the top-level param or config dict
    if target:
        config = {**(config or {}), "target": target}
    elif config and config.get("target"):
        target = config["target"]
    elif config and config.get("source_tool") and tool in CHAINABLE_TOOLS:
        # Chained scan — target comes from source_tool's report, not required here
        pass
    else:
        return {
            "status": "error",
            "error": (
                "A 'target' is required (e.g. target='example.com'). "
                f"Or set config.source_tool to chain from a previous scan "
                f"(supported for: {', '.join(CHAINABLE_TOOLS)})."
            ),
        }

    if tool not in SUPPORTED_TOOLS:
        return {
            "status": "error",
            "error": f"Unsupported tool: {tool}",
            "supported_tools": SUPPORTED_TOOLS,
        }

    try:
        # Auto-create virtual workspace if not provided

        if not workspace_id or workspace_id == "auto":
            logger.info("No workspace_id provided, creating virtual workspace for enumeration scan")

            workspace_service = get_workspace_service()

            workspace_result = workspace_service.create_workspace(
                source_type="virtual", source=f"enumeration-{tool}"
            )

            workspace_id = workspace_result["workspace_id"]

            logger.info(f"Created virtual workspace: {workspace_id}")

        service = _get_service_for_tool(tool)

        result = service.scan(workspace_id, scan_path, config)

        # Add workspace_id to result for reference

        if "workspace_id" not in result:
            result["workspace_id"] = workspace_id

        return result

    except Exception as e:
        logger.error(f"Scan failed for {tool}: {e}")

        return {"status": "error", "error": str(e)}


def _get_service_for_tool(tool: str):
    """Get the appropriate service instance for a tool."""

    if tool == "subfinder":
        return get_subfinder_service()

    if tool == "amass":
        return get_amass_service()

    if tool == "httpx":
        return get_httpx_service()

    if tool == "katana":
        return get_katana_service()

    if tool == "ffuf":
        return get_ffuf_service()

    if tool == "nmap":
        return get_nmap_service()

    if tool == "masscan":
        return get_masscan_service()

    if tool == "bbot":
        return get_bbot_service()

    if tool == "gau":
        return get_gau_service()

    if tool == "arjun":
        return get_arjun_service()

    if tool == "wafw00f":
        return get_wafw00f_service()

    if tool == "kiterunner":
        return get_kiterunner_service()

    raise ValueError(f"Unknown tool: {tool}")
