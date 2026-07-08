"""Shared helpers for DAST tool wrappers."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


def resolve_workspace_root(workspace_path: str) -> Path:
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2])
    return Path(workspace_path)


def scan_work_dir(workspace_root: Path, tool_name: str) -> Path:
    work_dir = workspace_root / "tmp" / tool_name
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir


def write_raw_request(raw_request: str, work_dir: Path, filename: str = "request.txt") -> Path:
    request_path = work_dir / filename
    request_path.write_text(raw_request, encoding="utf-8")
    return request_path


def write_findings(output_path: Path, findings: List[Dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(findings, handle, indent=2)


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def parse_url_parts(target: str) -> Dict[str, str]:
    parsed = urlparse(target if "://" in target else f"http://{target}")
    host = parsed.hostname or ""
    port = str(parsed.port or (443 if parsed.scheme == "https" else 80))
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return {"host": host, "port": port, "path": path, "url": target}


def finding(
    tool: str,
    title: str,
    severity: str = "medium",
    target: Optional[str] = None,
    detail: Optional[str] = None,
    evidence: Optional[str] = None,
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "tool": tool,
        "title": title,
        "severity": severity,
    }
    if target:
        entry["target"] = target
    if detail:
        entry["detail"] = detail
    if evidence:
        entry["evidence"] = evidence
    return entry
