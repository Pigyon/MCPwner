"""Reconnaissance chain tool — run multiple tools sequentially, passing results automatically."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from api.tools.reconnaissance.scan import AUTO_WORKSPACE, CHAINABLE_TOOLS, SUPPORTED_TOOLS
from config.tools import resolve_tool_name
from deps import get_service, get_workspace_repository, get_workspace_service

logger = logging.getLogger(__name__)

# How long a chain step will wait for a backgrounded scan's report to land
# before giving up and moving on (the scan keeps running in its tool container,
# but the chain falls back to the original target for the next step).
DEFAULT_BACKGROUND_WAIT_SECONDS = 240
BACKGROUND_POLL_INTERVAL_SECONDS = 3


def _report_dir(workspace_id: str, tool: str) -> Path:
    """Resolve the reconnaissance report directory for a tool in a workspace."""
    repo = get_workspace_repository()
    workspace = repo.find_by_id(workspace_id)
    reports_base = workspace.get_reports_base_dir() if workspace else f"/workspaces/{workspace_id}"
    return Path(f"{reports_base}/reports/reconnaissance/{tool}")


def _latest_report_path(workspace_id: str, tool: str) -> Optional[Path]:
    """Return the newest (non-cache) JSON report for a tool, or None."""
    report_dir = _report_dir(workspace_id, tool)
    if not report_dir.exists():
        return None
    reports = sorted(
        (p for p in report_dir.glob("*.json") if not p.name.startswith(".")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return reports[0] if reports else None


def _count_findings(report_path: Path) -> int:
    """Best-effort finding count from a report file."""
    try:
        with open(report_path, "r") as f:
            data = json.load(f)
    except Exception:
        return 0
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        # nmap-style {"hosts": [...]} — count open ports; otherwise treat as one record
        hosts = data.get("hosts")
        if isinstance(hosts, list):
            return sum(len(h.get("ports", [])) for h in hosts if isinstance(h, dict))
        return 1 if data else 0
    return 0


def _wait_for_fresh_report(
    workspace_id: str, tool: str, since: float, timeout: float
) -> Optional[Path]:
    """Poll for a report written at/after ``since`` (epoch seconds).

    A backgrounded scan keeps running in its tool container after the MCP client
    times out; its report is written atomically on completion. Polling the shared
    report volume lets the chain wait for that report instead of racing ahead and
    failing on a missing/stale file. Returns the report path, or None on timeout.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        latest = _latest_report_path(workspace_id, tool)
        # Allow a 1s slack so a report written essentially at scan-start still counts.
        if latest and latest.stat().st_mtime >= since - 1.0:
            return latest
        time.sleep(BACKGROUND_POLL_INTERVAL_SECONDS)
    return None


# Predefined common chains
PRESET_CHAINS = {
    "subdomain-to-params": ["subfinder", "httpx", "katana", "arjun"],
    "subdomain-to-waf": ["subfinder", "httpx", "wafw00f"],
    "subdomain-to-api": ["subfinder", "httpx", "kiterunner"],
    "subdomain-to-urls": ["subfinder", "gau", "arjun"],
    "osint-to-crawl": ["bbot", "httpx", "katana"],
    "network-to-http": ["nmap", "httpx"],
}


def _report_has_findings(workspace_id: str, tool: str) -> bool:
    """Check whether a tool's latest report in the workspace has at least one entry."""
    latest = _latest_report_path(workspace_id, tool)
    if not latest:
        return False
    return _count_findings(latest) > 0


def run_reconnaissance_chain(
    target: str,
    chain: List[str],
    workspace_id: Optional[str] = None,
    configs: Optional[Dict[str, Dict[str, Any]]] = None,
    preset: Optional[str] = None,
) -> Dict[str, Any]:
    """Run multiple reconnaissance tools sequentially, passing results between them automatically.

    Each tool in the chain reads from the previous tool's report via source_tool chaining.
    If a previous tool produced no findings, the chain falls back to the original target
    so downstream tools still run rather than failing with "no targets extracted".

    The chain always continues even if a step fails — partial results are returned.

    Args:
        target: The initial target domain, IP, or URL (e.g. "example.com").
        chain: Ordered list of tool names to run (e.g. ["subfinder", "httpx", "katana"]).
               Use preset instead to pick a predefined chain.
        workspace_id: UUID of the workspace. Auto-created if not provided.
                      Reuse across multiple chain calls to accumulate results.
        configs: Optional per-tool config overrides. Keys are tool names.
                 Example: {"httpx": {"tech_detect": true}, "ffuf": {"wordlist": "common"}}
        preset: Use a predefined chain instead of specifying 'chain' manually.
                Available presets:
                  subdomain-to-params  → subfinder → httpx → katana → arjun
                  subdomain-to-waf     → subfinder → httpx → wafw00f
                  subdomain-to-api     → subfinder → httpx → kiterunner
                  subdomain-to-urls    → subfinder → gau → arjun
                  osint-to-crawl       → bbot → httpx → katana
                  network-to-http      → nmap → httpx

    Returns:
        Dict with:
          - workspace_id: shared workspace for all steps
          - chain: the tools that were run
          - steps: per-step results with status, finding_count, error (if any)
          - summary: total findings, successful steps, failed steps
    """
    if preset:
        if preset not in PRESET_CHAINS:
            return {
                "status": "error",
                "error": f"Unknown preset '{preset}'. Available: {list(PRESET_CHAINS.keys())}",
            }
        chain = PRESET_CHAINS[preset]

    if not chain:
        return {"status": "error", "error": "chain must be a non-empty list of tool names."}

    chain = [resolve_tool_name(t) for t in chain]

    invalid = [t for t in chain if t not in SUPPORTED_TOOLS]
    if invalid:
        return {
            "status": "error",
            "error": f"Unknown tools in chain: {invalid}. Supported: {SUPPORTED_TOOLS}",
        }

    configs = configs or {}

    try:
        if not workspace_id or workspace_id == AUTO_WORKSPACE:
            workspace_service = get_workspace_service()
            workspace_result = workspace_service.create_workspace(
                source_type="virtual", source=f"chain-{'-'.join(chain[:3])}"
            )
            workspace_id = workspace_result["workspace_id"]
            logger.info(f"Created workspace for chain: {workspace_id}")

        steps = []
        total_findings = 0
        # Track the last successful tool that actually produced findings
        last_tool_with_findings: Optional[str] = None

        for i, tool in enumerate(chain):
            logger.info(f"Chain step {i + 1}/{len(chain)}: {tool}")

            tool_config = dict(configs.get(tool, {}))

            if i == 0:
                # First tool always gets the explicit target
                tool_config["target"] = target
            elif (
                tool in CHAINABLE_TOOLS and "target" not in tool_config and "targets" not in tool_config
            ):
                # Try to chain from the last tool that produced findings
                if last_tool_with_findings:
                    tool_config["source_tool"] = last_tool_with_findings
                    logger.info(f"{tool}: chaining from '{last_tool_with_findings}'")
                else:
                    # No previous tool had findings — fall back to original target
                    tool_config["target"] = target
                    logger.info(
                        f"{tool}: no previous findings to chain from, falling back to target='{target}'"
                    )
            elif "target" not in tool_config:
                tool_config["target"] = target

            try:
                service = get_service(tool)
                start = time.time()
                result = service.scan(workspace_id, None, tool_config)

                # A scan that exceeded the MCP client timeout returns
                # status="backgrounded" while still running in its tool
                # container. Wait for its report to land so the next step has
                # real input instead of failing on a missing/stale file.
                if result.get("status") == "backgrounded":
                    wait_timeout = tool_config.get(
                        "background_wait_seconds", DEFAULT_BACKGROUND_WAIT_SECONDS
                    )
                    logger.info(
                        f"{tool} backgrounded — waiting up to {wait_timeout}s for its report"
                    )
                    report = _wait_for_fresh_report(workspace_id, tool, start, wait_timeout)
                    if report:
                        result = {
                            "status": "success",
                            "finding_count": _count_findings(report),
                            "report_path": str(report),
                        }
                        logger.info(
                            f"{tool} report landed: {report} "
                            f"({result['finding_count']} findings)"
                        )
                    else:
                        logger.warning(
                            f"{tool} still backgrounded after {wait_timeout}s; "
                            f"next step will fall back to the original target"
                        )

                finding_count = result.get("finding_count", 0)
                total_findings += finding_count

                step_result = {
                    "tool": tool,
                    "status": result.get("status", "unknown"),
                    "finding_count": finding_count,
                    "input": tool_config.get("source_tool") or tool_config.get("target", target),
                }

                if result.get("status") == "error":
                    step_result["error"] = result.get("error", "Unknown error")
                    logger.warning(f"Step {tool} failed: {step_result['error']}")
                else:
                    # Only update last_tool_with_findings if this tool actually found something
                    # Always update the "last successful tool" regardless of finding count
                    # so the next step can at least attempt to chain
                    if _report_has_findings(workspace_id, tool):
                        last_tool_with_findings = tool
                        logger.info(f"{tool}: produced findings, will be used as source for next step")
                    else:
                        logger.info(
                            f"{tool}: succeeded but 0 findings — next step will use target fallback"
                        )

            except Exception as e:
                logger.error(f"Chain step {tool} raised exception: {e}")
                step_result = {
                    "tool": tool,
                    "status": "error",
                    "finding_count": 0,
                    "error": str(e),
                    "input": tool_config.get("source_tool") or tool_config.get("target", target),
                }

            steps.append(step_result)

        successful = [s for s in steps if s["status"] == "success"]
        failed = [s for s in steps if s["status"] == "error"]

        return {
            "status": "success" if successful else "error",
            "workspace_id": workspace_id,
            "chain": chain,
            "steps": steps,
            "summary": {
                "total_findings": total_findings,
                "successful_steps": len(successful),
                "failed_steps": len(failed),
                "completed_tools": [s["tool"] for s in successful],
                "failed_tools": [s["tool"] for s in failed],
            },
        }

    except Exception as e:
        logger.error(f"Chain execution failed: {e}")
        return {"status": "error", "error": str(e)}
