"""
gau Service - Get All URLs from Web Archives

gau fetches known URLs from web archives (Wayback Machine, Common Crawl, etc.)
for a given domain.

Config options:
  - target (required unless targets or source_tool is provided): Single domain to query
  - targets: List of domains to query in batch
  - source_tool: Name of a previous reconnaissance tool whose latest report should be used as input.
                 Extracts domains from the report automatically.
                 Supported source tools: subfinder, amass, bbot, httpx
  - providers: Comma-separated list of archive providers (e.g. "wayback,commoncrawl,otx,urlscan")
  - blacklist: Comma-separated list of extensions to blacklist (e.g. "ttf,woff,svg,png")
  - threads: Number of concurrent threads (integer)
  - from: Start date for filtering (format: YYYY-MM)
  - to: End date for filtering (format: YYYY-MM)
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from common.base_service import create_scanner_app
from common.models import ScanRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "gau"
VERSION_CMD = ["gau", "--version"]


def _resolve_workspace_root(workspace_path: str) -> Path:
    """Find the workspace root directory from a workspace path."""
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2])
    return Path(workspace_path)


def _extract_domain(value: str) -> str:
    """Extract bare domain from a URL or return the value as-is if already a domain."""
    value = value.strip()
    if value.startswith("http://") or value.startswith("https://"):
        try:
            return urlparse(value).hostname or value
        except Exception:
            return value
    # Strip port if present (e.g. "example.com:80" -> "example.com")
    return value.split(":")[0]


def _extract_targets_from_report(report_path: Path, source_tool: str) -> Set[str]:
    """Extract domains from a previous tool's JSON report."""
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
                    targets.add(_extract_domain(val))
                continue

            # subfinder: {"host": "sub.example.com", ...}
            if source_tool == "subfinder":
                if entry.get("host"):
                    targets.add(entry["host"])

            # amass: {"name": "sub.example.com", ...}
            elif source_tool == "amass":
                if entry.get("name"):
                    targets.add(entry["name"])

            # bbot: {"type": "DNS_NAME"|"URL"|"IP_ADDRESS", "data": "..."}
            elif source_tool == "bbot":
                etype = entry.get("type", "")
                edata = entry.get("data", "")
                if not isinstance(edata, str) or not edata:
                    continue
                if etype == "DNS_NAME":
                    targets.add(edata)
                elif etype == "URL":
                    targets.add(_extract_domain(edata))

            # httpx: {"url": "https://sub.example.com", "input": "sub.example.com", ...}
            elif source_tool == "httpx":
                url = entry.get("url") or entry.get("input", "")
                if url:
                    targets.add(_extract_domain(url))

            # Generic fallback
            else:
                for key in ("host", "domain", "name", "url", "target", "data"):
                    val = entry.get(key, "")
                    if isinstance(val, str) and val:
                        targets.add(_extract_domain(val))
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
    targets_dir = workspace_root / "tmp" / "gau"
    targets_dir.mkdir(parents=True, exist_ok=True)
    targets_file = Path(tempfile.mktemp(dir=str(targets_dir), suffix=".txt"))
    targets_file.write_text("\n".join(sorted(targets)) + "\n")
    return targets_file


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build gau scan command.

    Supports three input modes (checked in order):
      1. source_tool — auto-reads latest report from another tool in the workspace
      2. targets — explicit list of domains
      3. target — single domain

    gau accepts domains as positional arguments. For multiple targets we pass
    them all as positional args. Output is written to the output_path via --o.
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
                f"Run {source_tool} first, then chain with gau."
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
        all_targets.update(_extract_domain(t) for t in targets_list if t.strip())

    # Mode 3: Single target
    if single_target:
        all_targets.add(_extract_domain(single_target))

    if not all_targets:
        raise ValueError(
            "At least one target is required. Provide 'target' (single), "
            "'targets' (list), or 'source_tool' (auto-chain from previous scan) in config."
        )

    logger.info(f"Running gau against {len(all_targets)} domain(s)")

    # Build command: gau [options] domain1 domain2 ...
    # --o writes output to file; output is one URL per line (plain text / NDJSON-compatible)
    cmd = ["gau", "--o", str(output_path)]

    # Optional flags
    if config.get("providers"):
        cmd.extend(["--providers", str(config["providers"])])

    if config.get("blacklist"):
        cmd.extend(["--blacklist", str(config["blacklist"])])

    if config.get("threads"):
        cmd.extend(["--threads", str(config["threads"])])

    if config.get("from"):
        cmd.extend(["--from", str(config["from"])])

    if config.get("to"):
        cmd.extend(["--to", str(config["to"])])

    # Append all target domains as positional arguments
    cmd.extend(sorted(all_targets))

    return cmd


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json",
    tool_category="reconnaissance",
)
