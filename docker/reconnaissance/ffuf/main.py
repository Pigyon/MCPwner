"""
ffuf Service - Fast Web Fuzzer

Supports chaining: for example pass source_tool='httpx' (or katana, gau) to auto-extract
a base URL from a previous scan's report for fuzzing.

Available wordlists:
- /usr/share/wordlists/common.txt - Common files and directories
- /usr/share/wordlists/parameters.txt - Common HTTP parameters
- /usr/share/wordlists/subdomains.txt - Common subdomain names
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from common.base_service import create_scanner_app
from common.models import ScanRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "ffuf"
VERSION_CMD = ["ffuf", "-V"]

WORDLISTS = {
    "common": "/usr/share/wordlists/common.txt",
    "parameters": "/usr/share/wordlists/parameters.txt",
    "subdomains": "/usr/share/wordlists/subdomains.txt",
}


def _resolve_workspace_root(workspace_path: str) -> Path:
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2])
    return Path(workspace_path)


def _find_latest_report(workspace_root: Path, source_tool: str) -> Optional[Path]:
    report_dir = workspace_root / "reports" / "reconnaissance" / source_tool
    if not report_dir.exists():
        return None
    reports = sorted(report_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return reports[0] if reports else None


def _extract_base_url_from_report(report_path: Path, source_tool: str) -> Optional[str]:
    """Extract a single base URL from a previous tool's report for ffuf fuzzing."""
    try:
        with open(report_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                f.seek(0)
                data = [json.loads(line) for line in f if line.strip()]

        if not isinstance(data, list):
            data = [data]

        candidates: Set[str] = set()
        for entry in data:
            if not isinstance(entry, dict):
                val = str(entry).strip()
                if val.startswith("http://") or val.startswith("https://"):
                    candidates.add(val)
                continue

            if source_tool == "httpx":
                url = entry.get("url") or entry.get("input", "")
                if url:
                    candidates.add(url)
            elif source_tool == "katana":
                req = entry.get("request")
                if isinstance(req, dict) and req.get("endpoint"):
                    url = req["endpoint"]
                    if url.startswith("http://") or url.startswith("https://"):
                        candidates.add(url)
                elif entry.get("url"):
                    candidates.add(entry["url"])
                elif entry.get("endpoint"):
                    candidates.add(entry["endpoint"])
            elif source_tool == "gau":
                for key in ("url", "data"):
                    val = entry.get(key, "")
                    if isinstance(val, str) and val.startswith("http"):
                        candidates.add(val)
                        break

        if not candidates:
            return None

        # Return the shortest URL (most likely the base/root)
        return min(candidates, key=lambda u: len(u))

    except Exception as e:
        logger.warning(f"Failed to extract base URL from {report_path}: {e}")
        return None


def _get_base_url(url: str) -> str:
    """Strip path from URL to get scheme://host."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build ffuf scan command.

    Config options:
    - url/target: Target URL with FUZZ keyword (required, or derived from source_tool)
    - source_tool: Auto-extract base URL from a previous scan (httpx, katana, gau)
    - wordlist: Path to wordlist or name (common/parameters/subdomains)
    - extensions: Comma-separated file extensions (e.g., "php,html,js")
    - match_codes: HTTP status codes to match (e.g., "200,301")
    - filter_codes: HTTP status codes to filter out (e.g., "404")
    - match_size: Response size to match
    - filter_size: Response size to filter out
    - threads: Number of threads (default: 40)
    - rate: Requests per second limit
    - timeout: Request timeout in seconds
    - silent: Silent mode (boolean)
    """
    config: Dict[str, Any] = request.config or {}
    workspace_root = _resolve_workspace_root(request.workspace_path)

    # Resolve URL: explicit config takes priority, then source_tool
    url = config.get("url") or config.get("target", "")

    if not url and config.get("source_tool"):
        source_tool = config["source_tool"].strip()
        report_path = _find_latest_report(workspace_root, source_tool)
        if not report_path:
            raise ValueError(
                f"No report found for source tool '{source_tool}' in workspace. "
                f"Run {source_tool} first, then chain with ffuf."
            )
        base_url = _extract_base_url_from_report(report_path, source_tool)
        if not base_url:
            raise ValueError(
                f"Could not extract a base URL from {source_tool} report at {report_path}"
            )
        url = _get_base_url(base_url)
        logger.info(f"Derived base URL from {source_tool} report: {url}")

    if not url:
        raise ValueError(
            "URL is required for ffuf scan. Provide 'url'/'target' in config, "
            "or set 'source_tool' to chain from a previous scan (httpx, katana, gau)."
        )

    # Auto-add FUZZ keyword if missing
    if "FUZZ" not in url:
        if url.endswith("/"):
            url = url + "FUZZ"
        else:
            url = url + "/FUZZ"
        logger.info(f"Auto-added FUZZ keyword to URL: {url}")

    wordlist = "/usr/share/wordlists/common.txt"
    if "wordlist" in config:
        wordlist = WORDLISTS.get(config["wordlist"], config["wordlist"])

    cmd = ["ffuf", "-u", url, "-w", wordlist, "-o", str(output_path), "-of", "json"]

    if config.get("extensions"):
        cmd.extend(["-e", config["extensions"]])
    if config.get("match_codes"):
        cmd.extend(["-mc", config["match_codes"]])
    if config.get("filter_codes"):
        cmd.extend(["-fc", config["filter_codes"]])
    if config.get("match_size"):
        cmd.extend(["-ms", str(config["match_size"])])
    if config.get("filter_size"):
        cmd.extend(["-fs", str(config["filter_size"])])
    if config.get("threads"):
        cmd.extend(["-t", str(config["threads"])])
    if config.get("rate"):
        cmd.extend(["-rate", str(config["rate"])])
    if config.get("timeout"):
        cmd.extend(["-timeout", str(config["timeout"])])
    if config.get("silent", False):
        cmd.append("-s")

    return cmd


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json",
    tool_category="reconnaissance",
)
