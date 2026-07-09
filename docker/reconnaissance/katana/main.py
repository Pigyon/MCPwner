"""
Katana Service - Web Crawling Framework

Katana is a fast and configurable web crawling framework by ProjectDiscovery
for spidering and URL extraction.

Config options:
  - target (required unless targets or source_tool is provided): Single URL to crawl
  - targets: List of URLs/domains to crawl (e.g. ["https://example.com", "https://sub.example.com"])
  - source_tool: Name of a previous reconnaissance tool whose latest report should be used as input.
                 Extracts URLs/domains from the report automatically.
                 Supported source tools: subfinder, amass, bbot, httpx, nmap, masscan, ffuf, gau
  - depth: Crawl depth (integer, default: 3)
  - js_crawl: Enable JavaScript crawling (boolean, default: false)
  - headless: Enable headless browser mode (boolean, default: false)
  - scope: Crawl scope regex pattern (string)
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

TOOL_NAME = "katana"
VERSION_CMD = ["katana", "-version"]


def _resolve_workspace_root(workspace_path: str) -> Path:
    """Find the workspace root directory from a workspace path."""
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2])
    return Path(workspace_path)


def _extract_targets_from_report(report_path: Path, source_tool: str) -> Set[str]:
    """Extract URLs/domains from a previous tool's JSON report."""
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

            elif source_tool == "httpx":
                if entry.get("url"):
                    targets.add(entry["url"])
                elif entry.get("input"):
                    targets.add(entry["input"])

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

            elif source_tool == "gau":
                for key in ("url", "data"):
                    val = entry.get(key, "")
                    if isinstance(val, str) and val:
                        targets.add(val)
                        break

            else:
                for key in ("url", "host", "domain", "target", "ip", "name", "data"):
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


def _write_targets_file(targets: Set[str], workspace_root: Path) -> Path:
    """Write targets to a temporary file and return its path."""
    targets_dir = workspace_root / "tmp" / "katana"
    targets_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(targets_dir), suffix=".txt")
    targets_file = Path(tmp_path)
    os.close(fd)
    targets_file.write_text("\n".join(sorted(targets)) + "\n")
    return targets_file


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build katana scan command.

    Supports three input modes (checked in order, all can be combined):
      1. source_tool — auto-reads latest report from another tool in the workspace
      2. targets — explicit list of URLs/domains
      3. target — single URL/domain
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
                f"Run {source_tool} first, then chain with katana."
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

    logger.info(f"Final target count: {len(all_targets)}")

    cmd = ["katana", "-jsonl", "-o", str(output_path), "-silent"]

    if len(all_targets) == 1:
        cmd.extend(["-u", next(iter(all_targets))])
    else:
        targets_file = _write_targets_file(all_targets, workspace_root)
        logger.info(f"Wrote {len(all_targets)} targets to {targets_file}")
        cmd.extend(["-list", str(targets_file)])

    if config.get("depth"):
        cmd.extend(["-depth", str(config["depth"])])

    if config.get("js_crawl"):
        cmd.append("-js-crawl")

    if config.get("headless"):
        cmd.append("-headless")

    if config.get("scope"):
        cmd.extend(["-field-scope", str(config["scope"])])

    return cmd


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json",
    tool_category="reconnaissance",
)
