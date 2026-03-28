"""
Kiterunner Service - Context-Aware Content Discovery

Kiterunner is a context-aware content discovery tool by Assetnote that uses
API-aware wordlists to find API endpoints and routes.

Config options:
  - target (required unless targets or source_tool is provided): Single URL/host to scan
  - targets: List of URLs/hosts to scan in batch (written to temp file, fed via --targets)
  - source_tool: Name of a previous reconnaissance tool whose latest report should be used as input.
                 Extracts URLs/hosts from the report automatically.
                 Supported source tools: httpx, katana, gau, subfinder, amass, bbot
  - wordlist: Path to an API-aware wordlist file (kiterunner .kite format or plain text)
  - threads: Number of concurrent threads (integer)
  - max_connection_per_host: Maximum connections per host (integer)
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from common.base_service import create_scanner_app
from common.models import ScanRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "kiterunner"
VERSION_CMD = ["kr", "version"]


def _resolve_workspace_root(workspace_path: str) -> Path:
    """Find the workspace root directory from a workspace path."""
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2])
    return Path(workspace_path)


def _extract_targets_from_report(report_path: Path, source_tool: str) -> Set[str]:
    """Extract URLs/hosts from a previous tool's JSON report.

    For kiterunner, URL-type and host-type targets are both useful since it
    discovers API endpoints on web servers.
    """
    targets: Set[str] = set()
    try:
        with open(report_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                # Try NDJSON
                f.seek(0)
                data = [json.loads(line) for line in f if line.strip()]

        if not isinstance(data, list):
            data = [data]

        for entry in data:
            if not isinstance(entry, dict):
                # Plain string — could be a raw URL (e.g. from gau)
                val = str(entry).strip()
                if val and (val.startswith("http://") or val.startswith("https://")):
                    targets.add(val)
                continue

            # httpx: {"url": "https://example.com/path", ...}
            if source_tool == "httpx":
                if entry.get("url"):
                    targets.add(entry["url"])
                elif entry.get("input"):
                    targets.add(entry["input"])

            # katana: {"url": "https://...", "endpoint": "..."}
            elif source_tool == "katana":
                if entry.get("url"):
                    targets.add(entry["url"])
                elif entry.get("endpoint"):
                    targets.add(entry["endpoint"])

            # gau: plain URL strings (line-delimited), handled above as non-dict
            # but also handle if wrapped in a dict
            elif source_tool == "gau":
                for key in ("url", "data"):
                    val = entry.get(key, "")
                    if isinstance(val, str) and val.startswith("http"):
                        targets.add(val)
                        break

            # subfinder: {"host": "sub.example.com", ...}
            elif source_tool == "subfinder":
                if entry.get("host"):
                    targets.add(entry["host"])

            # amass: {"name": "sub.example.com", ...}
            elif source_tool == "amass":
                if entry.get("name"):
                    targets.add(entry["name"])

            # bbot: prefer URL type events, also accept DNS_NAME and OPEN_TCP_PORT
            elif source_tool == "bbot":
                etype = entry.get("type", "")
                edata = entry.get("data", "")
                if not isinstance(edata, str) or not edata:
                    continue
                if etype == "URL":
                    targets.add(edata)
                elif etype == "DNS_NAME":
                    targets.add(edata)
                elif etype == "OPEN_TCP_PORT":
                    try:
                        host, port_str = edata.rsplit(":", 1)
                        port = int(port_str)
                        scheme = "https" if port in (443, 8443, 4443) else "http"
                        targets.add(f"{scheme}://{host}:{port}")
                    except (ValueError, AttributeError):
                        pass

            # Generic fallback: try URL-like fields first, then host/name
            else:
                for key in ("url", "endpoint", "data"):
                    val = entry.get(key, "")
                    if isinstance(val, str) and val.startswith("http"):
                        targets.add(val)
                        break
                else:
                    for key in ("host", "name", "domain"):
                        val = entry.get(key, "")
                        if isinstance(val, str) and val.strip():
                            targets.add(val)
                            break

    except Exception as e:
        logger.warning(f"Failed to extract targets from {report_path}: {e}")

    return targets


def _find_latest_report(workspace_root: Path, source_tool: str) -> Optional[Path]:
    """Find the latest report file from a source tool in the workspace."""
    report_dir = workspace_root / "reports" / "reconnaissance" / source_tool
    if not report_dir.exists():
        return None
    reports = sorted(report_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return reports[0] if reports else None


def _write_targets_file(targets: Set[str], workspace_root: Path) -> Path:
    """Write targets to a temporary file and return its path."""
    targets_dir = workspace_root / "tmp" / "kiterunner"
    targets_dir.mkdir(parents=True, exist_ok=True)
    targets_file = Path(tempfile.mktemp(dir=str(targets_dir), suffix=".txt"))
    targets_file.write_text("\n".join(sorted(targets)) + "\n")
    return targets_file


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build kiterunner scan command.

    Supports three input modes (checked in order, all can be combined):
      1. source_tool — auto-reads latest report from another tool in the workspace
      2. targets — explicit list of URLs/hosts to scan
      3. target — single URL/host to scan
    """
    config: Dict[str, Any] = request.config or {}
    workspace_root = _resolve_workspace_root(request.workspace_path)

    source_tool = config.get("source_tool", "").strip()
    targets_list: List[str] = config.get("targets", [])
    single_target = config.get("target", "").strip()

    all_targets: Set[str] = set()

    # Mode 1: Auto-chain from a previous tool's report
    if source_tool:
        report_path = _find_latest_report(workspace_root, source_tool)
        if not report_path:
            raise ValueError(
                f"No report found for source tool '{source_tool}' in workspace. "
                f"Run {source_tool} first, then chain with kiterunner."
            )
        extracted = _extract_targets_from_report(report_path, source_tool)
        if not extracted:
            raise ValueError(
                f"Could not extract any targets from {source_tool} report at {report_path}"
            )
        logger.info(f"Extracted {len(extracted)} targets from {source_tool} report")
        all_targets.update(extracted)

    # Mode 2: Explicit target list
    if targets_list:
        all_targets.update(t.strip() for t in targets_list if t.strip())

    # Mode 3: Single target
    if single_target:
        all_targets.add(single_target)

    if not all_targets:
        raise ValueError(
            "At least one target is required. Provide 'target' (single URL/host), "
            "'targets' (list of URLs/hosts), or 'source_tool' (auto-chain from previous scan) in config."
        )

    logger.info(f"Running kiterunner against {len(all_targets)} target(s)")

    # Build base command — kr scan with JSON output
    cmd = ["kr", "scan"]

    # Input: single target as positional arg, multiple via --targets file
    if len(all_targets) == 1:
        cmd.append(next(iter(all_targets)))
    else:
        targets_file = _write_targets_file(all_targets, workspace_root)
        logger.info(f"Wrote {len(all_targets)} targets to {targets_file}")
        cmd.extend(["--targets", str(targets_file)])

    # Output format
    cmd.extend(["--output", "json"])

    # Optional flags
    if config.get("wordlist"):
        cmd.extend(["-w", str(config["wordlist"])])

    if config.get("threads"):
        cmd.extend(["--threads", str(config["threads"])])

    if config.get("max_connection_per_host"):
        cmd.extend(["--max-connection-per-host", str(config["max_connection_per_host"])])

    return cmd


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json",
    tool_category="reconnaissance",
)
