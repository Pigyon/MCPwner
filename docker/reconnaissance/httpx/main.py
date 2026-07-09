"""
httpx Service - HTTP Toolkit for Probing and Analysis

httpx is a fast and multi-purpose HTTP toolkit by ProjectDiscovery
that allows probing and analysis of web servers.

Config options:
  - target (required unless targets or source_tool is provided): Single URL, domain, or IP to probe
  - targets: List of URLs/domains/IPs to probe in batch (e.g. ["sub1.example.com", "sub2.example.com"])
  - source_tool: Name of a previous reconnaissance tool whose latest report should be used as input.
                 Extracts domains/URLs/IPs from the report automatically.
                 Supported source tools: subfinder, amass, bbot, nmap, masscan, ffuf
  - status_code: Filter by HTTP status code (e.g. "200" or "200,301,302")
  - tech_detect: Enable technology detection (boolean, default: false)
  - follow_redirects: Follow HTTP redirects (boolean, default: false)
  - threads: Number of concurrent threads (integer)
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from common.base_service import create_scanner_app
from common.models import ScanRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "httpx"
VERSION_CMD = ["httpx", "-version"]


def _resolve_workspace_root(workspace_path: str) -> Path:
    """Find the workspace root directory from a workspace path."""
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2])
    return Path(workspace_path)


def _extract_targets_from_report(report_path: Path, source_tool: str) -> Set[str]:
    """Extract domains/URLs/IPs from a previous tool's JSON report."""
    targets: Set[str] = set()
    try:
        with open(report_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                f.seek(0)
                data = [json.loads(line) for line in f if line.strip()]

        if not isinstance(data, list):
            data = [data]

        for entry in data:
            if not isinstance(entry, dict):
                val = str(entry).strip()
                if val:
                    targets.add(val)
                continue

            if source_tool == "subfinder":
                if entry.get("host"):
                    targets.add(entry["host"])

            elif source_tool == "amass":
                # amass writes {"subdomain": "..."}; raw/older formats use "name"
                val = entry.get("subdomain") or entry.get("name")
                if val:
                    targets.add(val)

            # OPEN_TCP_PORT data is "ip:port" (e.g. "45.33.32.156:80") — normalize to http(s)://
            elif source_tool == "bbot":
                etype = entry.get("type", "")
                edata = entry.get("data", "")
                if not isinstance(edata, str) or not edata:
                    continue
                if etype == "URL" or etype in ("DNS_NAME", "IP_ADDRESS"):
                    targets.add(edata)
                elif etype == "OPEN_TCP_PORT":
                    try:
                        host, port_str = edata.rsplit(":", 1)
                        port = int(port_str)
                        scheme = "https" if port in (443, 8443, 4443) else "http"
                        targets.add(f"{scheme}://{host}:{port}")
                    except (ValueError, AttributeError):
                        targets.add(edata)

            elif source_tool in ("nmap", "masscan"):
                host = entry.get("ip") or entry.get("host") or entry.get("addr", "")
                if host:
                    port = entry.get("port")
                    if port:
                        port = int(port)
                        scheme = "https" if port in (443, 8443, 4443) else "http"
                        targets.add(f"{scheme}://{host}:{port}")
                    else:
                        targets.add(host)

            elif source_tool == "ffuf":
                if "results" in entry:
                    for r in entry["results"]:
                        if isinstance(r, dict) and r.get("url"):
                            targets.add(r["url"])
                elif entry.get("url"):
                    targets.add(entry["url"])

            else:
                for key in ("host", "url", "domain", "target", "ip", "name", "data"):
                    val = entry.get(key, "")
                    if isinstance(val, str) and val:
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

    reports = sorted(
        (p for p in report_dir.glob("*.json") if not p.name.startswith(".")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return reports[0] if reports else None


def _deduplicate_targets(targets: Set[str]) -> Set[str]:
    """Remove bare domains/IPs that are already represented by a full URL in the set.

    e.g. if both "scanme.nmap.org" and "http://scanme.nmap.org/" are present,
    keep only the full URL. Also normalizes by stripping trailing slashes from URLs.
    """
    normalized: Set[str] = set()
    for t in targets:
        normalized.add(t.rstrip("/"))

    covered_hosts: Set[str] = set()
    for t in normalized:
        if t.startswith("http://") or t.startswith("https://"):
            try:
                without_scheme = t.split("://", 1)[1]
                host = without_scheme.split("/")[0].split(":")[0]
                covered_hosts.add(host)
            except IndexError:
                pass

    result: Set[str] = set()
    for t in normalized:
        if t.startswith("http://") or t.startswith("https://"):
            result.add(t)
        else:
            bare_host = t.split(":")[0]  # strip port if present
            if bare_host not in covered_hosts:
                result.add(t)

    return result


def _write_targets_file(targets: Set[str], workspace_root: Path) -> Path:
    """Write targets to a temporary file and return its path."""
    targets_dir = workspace_root / "tmp" / "httpx"
    targets_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(targets_dir), suffix=".txt")
    targets_file = Path(tmp_path)
    os.close(fd)
    targets_file.write_text("\n".join(sorted(targets)) + "\n")
    return targets_file


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build httpx scan command.

    Supports three input modes (checked in order):
      1. source_tool — auto-reads latest report from another tool in the workspace
      2. targets — explicit list of URLs/domains/IPs
      3. target — single URL/domain/IP
    """
    config: Dict[str, Any] = request.config or {}
    workspace_root = _resolve_workspace_root(request.workspace_path)

    source_tool = config.get("source_tool", "").strip()
    targets_list: List[str] = config.get("targets", [])
    single_target = config.get("target", "").strip()

    all_targets: Set[str] = set()

    if source_tool:
        report_path = _find_latest_report(workspace_root, source_tool)
        if not report_path:
            raise ValueError(
                f"No report found for source tool '{source_tool}' in workspace. "
                f"Run {source_tool} first, then chain with httpx."
            )
        extracted = _extract_targets_from_report(report_path, source_tool)
        if not extracted:
            raise ValueError(f"Could not extract any targets from {source_tool} report at {report_path}")
        logger.info(f"Extracted {len(extracted)} targets from {source_tool} report")
        all_targets.update(extracted)

    if targets_list:
        all_targets.update(t.strip() for t in targets_list if t.strip())

    if single_target:
        all_targets.add(single_target)

    if not all_targets:
        raise ValueError(
            "At least one target is required. Provide 'target' (single), "
            "'targets' (list), or 'source_tool' (auto-chain from previous scan) in config."
        )

    all_targets = _deduplicate_targets(all_targets)
    logger.info(f"Final deduplicated target count: {len(all_targets)}")

    if len(all_targets) == 1:
        cmd = ["httpx", "-u", next(iter(all_targets)), "-json", "-o", str(output_path), "-silent"]
    else:
        targets_file = _write_targets_file(all_targets, workspace_root)
        logger.info(f"Wrote {len(all_targets)} targets to {targets_file}")
        cmd = ["httpx", "-l", str(targets_file), "-json", "-o", str(output_path), "-silent"]

    if config.get("status_code"):
        cmd.extend(["-mc", str(config["status_code"])])

    if config.get("tech_detect"):
        cmd.append("-tech-detect")

    if config.get("follow_redirects"):
        cmd.append("-follow-redirects")

    if config.get("threads"):
        cmd.extend(["-threads", str(config["threads"])])

    return cmd


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json",
    tool_category="reconnaissance",
)
