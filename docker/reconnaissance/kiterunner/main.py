"""
Kiterunner Service - Context-Aware Content Discovery

Kiterunner is a context-aware content discovery tool by Assetnote that uses
API-aware wordlists to find API endpoints and routes.

Config options:
  - target (required unless targets or source_tool is provided): Single URL/host to scan
  - targets: List of URLs/hosts to scan in batch (written to temp file, fed via file: prefix)
  - source_tool: Name of a previous reconnaissance tool whose latest report should be used as input.
                 Extracts URLs/hosts from the report automatically.
                 Supported source tools: httpx, katana, gau, subfinder, amass, bbot
  - wordlist: Path to an API-aware wordlist file (kiterunner .kite format or plain text)
  - threads: Number of concurrent threads (integer)
  - max_connection_per_host: Maximum connections per host (integer)

Note: kiterunner (kr) has no --output-file flag; output is captured from stdout.
"""

import json
import logging
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from common.models import HealthResponse, ScanRequest, VersionResponse
from fastapi import FastAPI, HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "kiterunner"
VERSION_CMD = ["kr", "version"]

app = FastAPI(title="Kiterunner Service", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy", "service": TOOL_NAME}


@app.get("/version", response_model=VersionResponse)
def version():
    try:
        result = subprocess.run(VERSION_CMD, capture_output=True, text=True, timeout=5, check=True)
        return {"version": result.stdout.strip(), "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _resolve_workspace_root(workspace_path: str) -> Path:
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2])
    return Path(workspace_path)


def _extract_targets_from_report(report_path: Path, source_tool: str) -> Set[str]:
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
                if val and (val.startswith("http://") or val.startswith("https://")):
                    targets.add(val)
                continue

            if source_tool == "httpx":
                if entry.get("url"):
                    targets.add(entry["url"])
                elif entry.get("input"):
                    targets.add(entry["input"])
            elif source_tool == "katana":
                req = entry.get("request")
                if isinstance(req, dict) and req.get("endpoint"):
                    url = req["endpoint"]
                    if url.startswith("http://") or url.startswith("https://"):
                        targets.add(url)
                elif entry.get("url"):
                    targets.add(entry["url"])
                elif entry.get("endpoint"):
                    targets.add(entry["endpoint"])
            elif source_tool == "gau":
                for key in ("url", "data"):
                    val = entry.get(key, "")
                    if isinstance(val, str) and val.startswith("http"):
                        targets.add(val)
                        break
            elif source_tool == "subfinder":
                if entry.get("host"):
                    targets.add(entry["host"])
            elif source_tool == "amass":
                if entry.get("name"):
                    targets.add(entry["name"])
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
    report_dir = workspace_root / "reports" / "reconnaissance" / source_tool
    if not report_dir.exists():
        return None
    reports = sorted(report_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return reports[0] if reports else None


def _write_targets_file(targets: Set[str], workspace_root: Path) -> Path:
    targets_dir = workspace_root / "tmp" / "kiterunner"
    targets_dir.mkdir(parents=True, exist_ok=True)
    targets_file = Path(tempfile.mktemp(dir=str(targets_dir), suffix=".txt"))
    targets_file.write_text("\n".join(sorted(targets)) + "\n")
    return targets_file


@app.post("/scan")
def scan(request: ScanRequest):
    """Execute kiterunner scan. Captures stdout since kr has no --output-file flag."""
    try:
        config: Dict[str, Any] = request.config or {}
        workspace_root = _resolve_workspace_root(request.workspace_path)

        source_tool = config.get("source_tool", "").strip()
        targets_list: List[str] = config.get("targets", [])
        single_target = config.get("target", "").strip()

        all_targets: Set[str] = set()

        if source_tool:
            report_path = _find_latest_report(workspace_root, source_tool)
            if not report_path:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"No report found for source tool '{source_tool}' in workspace. "
                        f"Run {source_tool} first, then chain with kiterunner."
                    ),
                )
            extracted = _extract_targets_from_report(report_path, source_tool)
            if not extracted:
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not extract any targets from {source_tool} report at {report_path}",
                )
            logger.info(f"Extracted {len(extracted)} targets from {source_tool} report")
            all_targets.update(extracted)

        if targets_list:
            all_targets.update(t.strip() for t in targets_list if t.strip())

        if single_target:
            all_targets.add(single_target)

        if not all_targets:
            raise HTTPException(
                status_code=400,
                detail=(
                    "At least one target is required. Provide 'target' (single URL/host), "
                    "'targets' (list), or 'source_tool' (auto-chain from previous scan) in config."
                ),
            )

        logger.info(f"Running kiterunner against {len(all_targets)} target(s)")

        # Build command — kr outputs to stdout only, no file flag
        cmd = ["kr", "scan", "-o", "json"]

        if config.get("wordlist"):
            cmd.extend(["-w", str(config["wordlist"])])
        if config.get("threads"):
            cmd.extend(["--threads", str(config["threads"])])
        if config.get("max_connection_per_host"):
            cmd.extend(["--max-connection-per-host", str(config["max_connection_per_host"])])

        # Single target as positional arg; multiple via file: prefix
        if len(all_targets) == 1:
            cmd.append(next(iter(all_targets)))
        else:
            targets_file = _write_targets_file(all_targets, workspace_root)
            logger.info(f"Wrote {len(all_targets)} targets to {targets_file}")
            cmd.append(f"file:{targets_file}")

        # Create output directory and path
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        output_dir = workspace_root / "reports" / "reconnaissance" / TOOL_NAME
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}.json"

        logger.info(f"Executing kiterunner: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        # kr outputs JSON lines to stdout; write them to the report file
        stdout = result.stdout.strip()
        if not stdout:
            output_path.write_text("[]")
            return {
                "status": "success",
                "finding_count": 0,
                "report_path": str(output_path),
                "timestamp": timestamp,
            }

        # Parse NDJSON and convert to JSON array
        lines = [line for line in stdout.splitlines() if line.strip()]
        try:
            findings = [json.loads(line) for line in lines]
        except json.JSONDecodeError:
            findings = [{"raw": line} for line in lines]

        with open(output_path, "w") as f:
            json.dump(findings, f, indent=2)

        return {
            "status": "success",
            "finding_count": len(findings),
            "report_path": str(output_path),
            "timestamp": timestamp,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Kiterunner scan error")
        raise HTTPException(status_code=500, detail=str(e))
