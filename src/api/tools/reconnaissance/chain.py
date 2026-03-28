"""Reconnaissance chain tool — run multiple tools sequentially, passing results automatically."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from deps import get_workspace_service
from api.tools.reconnaissance.scan import SUPPORTED_TOOLS, CHAINABLE_TOOLS, _get_service_for_tool

logger = logging.getLogger(__name__)

# Valid chain edges: which tools can feed into which
CHAIN_EDGES = {
    "subfinder": ["httpx", "katana", "gau", "wafw00f", "kiterunner", "amass"],
    "amass":     ["httpx", "katana", "gau", "wafw00f", "kiterunner"],
    "bbot":      ["httpx", "katana", "gau", "wafw00f", "kiterunner", "arjun"],
    "httpx":     ["katana", "arjun", "wafw00f", "kiterunner", "gau", "ffuf"],
    "katana":    ["arjun", "kiterunner", "ffuf"],
    "gau":       ["arjun", "kiterunner", "ffuf"],
    "ffuf":      [],
    "arjun":     [],
    "wafw00f":   [],
    "kiterunner": [],
    "nmap":      ["httpx"],
    "masscan":   ["httpx"],
}

# Predefined common chains
PRESET_CHAINS = {
    "subdomain-to-params": ["subfinder", "httpx", "katana", "arjun"],
    "subdomain-to-waf":    ["subfinder", "httpx", "wafw00f"],
    "subdomain-to-api":    ["subfinder", "httpx", "kiterunner"],
    "subdomain-to-urls":   ["subfinder", "gau", "arjun"],
    "osint-to-crawl":      ["bbot", "httpx", "katana"],
    "network-to-http":     ["nmap", "httpx"],
}


def _report_has_findings(workspace_id: str, tool: str) -> bool:
    """Check whether a tool's latest report in the workspace has at least one entry."""
    report_dir = Path(f"/workspaces/{workspace_id}/reports/reconnaissance/{tool}")
    if not report_dir.exists():
        return False
    reports = sorted(report_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not reports:
        return False
    try:
        with open(reports[0], "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return len(data) > 0
        return bool(data)
    except Exception:
        return False


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

    invalid = [t for t in chain if t not in SUPPORTED_TOOLS]
    if invalid:
        return {
            "status": "error",
            "error": f"Unknown tools in chain: {invalid}. Supported: {SUPPORTED_TOOLS}",
        }

    configs = configs or {}

    try:
        if not workspace_id or workspace_id == "auto":
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
            elif tool in CHAINABLE_TOOLS and "target" not in tool_config and "targets" not in tool_config:
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
                service = _get_service_for_tool(tool)
                result = service.scan(workspace_id, None, tool_config)

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
                        logger.info(f"{tool}: succeeded but 0 findings — next step will use target fallback")

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
