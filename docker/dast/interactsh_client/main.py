"""
Interactsh client DAST service.

Runs interactsh-client persistently in a background thread to generate an OOB
interaction domain. The /scan endpoint snapshots current interactions and
writes a per-workspace report scoped to interactions received since the last
scan in that workspace.

The startup is non-blocking: the interactsh process is spawned in a daemon
thread so it doesn't block uvicorn's event loop.

Config options:
  - (none required) — call /scan to snapshot interactions and get the OOB domain
"""

import json
import logging
import re
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from common.models import HealthResponse, ScanRequest, VersionResponse
from fastapi import FastAPI, HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "interactsh-client"
TOOL_CATEGORY = "dast"
INTERACTIONS_PATH = Path("/tmp/interactions.jsonl")
INTERACTSH_BIN = "interactsh-client"

app = FastAPI(title="Interactsh Client Service", version="1.0.0")

_interactsh_process: Optional[subprocess.Popen] = None
_interactsh_domain: Optional[str] = None
_lock = threading.Lock()
_last_scan_offset: Dict[str, int] = {}
_startup_complete = threading.Event()


def _start_interactsh() -> None:
    global _interactsh_process, _interactsh_domain
    with _lock:
        if _interactsh_process and _interactsh_process.poll() is None:
            return
        INTERACTIONS_PATH.unlink(missing_ok=True)
        _interactsh_process = subprocess.Popen(
            [INTERACTSH_BIN, "-json", "-o", str(INTERACTIONS_PATH)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )


def _read_domain_thread() -> None:
    """Read interactsh stdout in a daemon thread to capture the OOB domain."""
    global _interactsh_domain
    _start_interactsh()
    proc = _interactsh_process
    if not proc or not proc.stdout:
        _startup_complete.set()
        return
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        match = re.search(r"([a-z0-9]+\.[a-z0-9]+\.[a-z]{2,})", line, re.IGNORECASE)
        if match and "oast" in match.group(1).lower():
            _interactsh_domain = match.group(1)
            logger.info("Interactsh domain: %s", _interactsh_domain)
            _startup_complete.set()
            break
    _startup_complete.set()
    if proc.stdout:
        for _ in proc.stdout:
            pass


@app.on_event("startup")
def startup_event():
    t = threading.Thread(target=_read_domain_thread, daemon=True)
    t.start()


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy", "service": TOOL_NAME}


@app.get("/version", response_model=VersionResponse)
def version():
    try:
        result = subprocess.run(
            [INTERACTSH_BIN, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        value = re.sub(r"\x1b\[[0-9;]*m", "", (result.stdout + result.stderr)).strip()
        ver_match = re.search(r"Version:\s*(\S+)", value)
        return {
            "version": ver_match.group(1) if ver_match else value.split("\n")[-1],
            "status": "success",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/domain")
def get_domain():
    _startup_complete.wait(timeout=30)
    return {"status": "success", "domain": _interactsh_domain}


def _resolve_report_dir(workspace_path: str, report_base: Optional[str] = None) -> Path:
    if report_base:
        return Path(report_base) / "reports" / TOOL_CATEGORY / TOOL_NAME
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2]) / "reports" / TOOL_CATEGORY / TOOL_NAME
    return Path(workspace_path).parent / "reports" / TOOL_CATEGORY / TOOL_NAME


def _load_interactions_since(offset: int) -> List[Dict[str, Any]]:
    if not INTERACTIONS_PATH.exists():
        return []
    interactions: List[Dict[str, Any]] = []
    with open(INTERACTIONS_PATH, "r", encoding="utf-8", errors="ignore") as fh:
        fh.seek(offset)
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                interactions.append(json.loads(line))
            except json.JSONDecodeError:
                interactions.append({"raw": line})
    return interactions


def _current_file_size() -> int:
    try:
        return INTERACTIONS_PATH.stat().st_size
    except FileNotFoundError:
        return 0


def _workspace_key(workspace_path: str) -> str:
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return workspace_path


@app.post("/scan")
def scan(request: ScanRequest):
    full_scan_path = Path(request.workspace_path) / request.scan_path
    if not full_scan_path.exists():
        raise HTTPException(status_code=404, detail=f"Scan path does not exist: {full_scan_path}")

    _startup_complete.wait(timeout=30)

    ws_key = _workspace_key(request.workspace_path)
    offset = _last_scan_offset.get(ws_key, 0)
    interactions = _load_interactions_since(offset)
    _last_scan_offset[ws_key] = _current_file_size()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
    output_dir = _resolve_report_dir(request.workspace_path, request.report_base)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{timestamp}.json"

    report = {"domain": _interactsh_domain, "interactions": interactions}
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    return {
        "status": "success",
        "finding_count": len(interactions),
        "report_path": str(output_path),
        "timestamp": timestamp,
        "domain": _interactsh_domain,
    }


@app.get("/reports")
def list_reports(workspace_path: str, report_base: Optional[str] = None):
    report_dir = _resolve_report_dir(workspace_path, report_base)
    if not report_dir.exists():
        return {"status": "success", "reports": []}
    reports = sorted([p.stem for p in report_dir.iterdir() if p.is_file()], reverse=True)
    return {"status": "success", "reports": reports}


@app.get("/report/{timestamp}")
def get_report(timestamp: str, workspace_path: str, report_base: Optional[str] = None):
    report_dir = _resolve_report_dir(workspace_path, report_base)
    candidate = report_dir / f"{timestamp}.json"
    if not candidate.exists():
        raise HTTPException(status_code=404, detail=f"No report found for timestamp '{timestamp}'")
    with open(candidate, encoding="utf-8") as handle:
        data = json.load(handle)
    return {"status": "success", "report": data, "report_path": str(candidate)}
