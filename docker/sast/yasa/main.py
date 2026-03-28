from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest

# YASA language map: normalise incoming language names to what YASA accepts
_LANG_MAP = {
    "javascript": "javascript",
    "typescript": "javascript",  # YASA treats TS as JS
    "js": "javascript",
    "ts": "javascript",
    "go": "golang",
    "golang": "golang",
    "java": "java",
    "python": "python",
}

# Languages YASA auto-detects when --language is omitted; we still require it
# for clarity, but fall back to auto-detection if not provided.
_SUPPORTED = set(_LANG_MAP.keys())


def build_yasa_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path
    config = request.config or {}

    # YASA writes findings.sarif into the report directory; output_path IS
    # that directory (base_service passes a file path, so we use its parent
    # and rename afterwards in a post-processing step — see note below).
    # We pass the directory as --report and let YASA name the file itself.
    report_dir = output_path.parent

    cmd = [
        "yasa",
        "--sourcePath", str(full_scan_path),
        "--report", str(report_dir),
        "--format", "sarif",
    ]

    # Language: explicit > config > auto-detect
    lang = config.get("language", "")
    if lang:
        mapped = _LANG_MAP.get(lang.lower())
        if not mapped:
            raise ValueError(
                f"Unsupported language '{lang}'. "
                f"Supported: {', '.join(sorted(_SUPPORTED))}"
            )
        cmd.extend(["--language", mapped])

    if "analyzer" in config:
        cmd.extend(["--analyzer", config["analyzer"]])

    if "checkerIds" in config:
        cmd.extend(["--checkerIds", ",".join(config["checkerIds"])])

    if "checkerPackIds" in config:
        cmd.extend(["--checkerPackIds", ",".join(config["checkerPackIds"])])

    if config.get("ruleConfigFile"):
        cmd.extend(["--ruleConfigFile", config["ruleConfigFile"]])

    return cmd


# YASA names its output file "findings.sarif" inside the report dir.
# base_service expects the report at `output_path` exactly, so we subclass
# the app and override /scan to handle YASA's naming convention.

import json
import logging
import subprocess
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)

app = FastAPI(title="YASA Service", version="1.0.0")

from common.models import HealthResponse, VersionResponse


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy", "service": "yasa"}


@app.get("/version", response_model=VersionResponse)
def version():
    try:
        result = subprocess.run(
            ["yasa", "--version"],
            capture_output=True, text=True, timeout=10, check=False,
        )
        ver = result.stdout.strip() or result.stderr.strip() or "v0.2.33"
        return {"version": ver, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan")
def scan(request: ScanRequest):
    try:
        full_scan_path = Path(request.workspace_path) / request.scan_path

        if not full_scan_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Scan path does not exist: {full_scan_path}",
            )

        # Build output directory
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        parts = Path(request.workspace_path).parts
        if "workspaces" in parts:
            idx = parts.index("workspaces")
            if idx + 1 < len(parts):
                workspace_root = Path(*parts[: idx + 2])
                report_dir = workspace_root / "reports" / "sast" / "yasa" / timestamp
            else:
                report_dir = Path(request.workspace_path) / "reports" / "sast" / "yasa" / timestamp
        else:
            report_dir = Path(request.workspace_path).parent / "reports" / "sast" / "yasa" / timestamp

        report_dir.mkdir(parents=True, exist_ok=True)

        config = request.config or {}

        # Build command
        cmd = ["yasa", "--sourcePath", str(full_scan_path),
               "--report", str(report_dir), "--format", "sarif"]

        lang = config.get("language", "")
        if lang:
            mapped = _LANG_MAP.get(lang.lower())
            if not mapped:
                return {"status": "error",
                        "error": f"Unsupported language '{lang}'. Supported: {', '.join(sorted(_SUPPORTED))}"}
            cmd.extend(["--language", mapped])

        if "analyzer" in config:
            cmd.extend(["--analyzer", config["analyzer"]])
        if "checkerIds" in config:
            cmd.extend(["--checkerIds", ",".join(config["checkerIds"])])
        if "checkerPackIds" in config:
            cmd.extend(["--checkerPackIds", ",".join(config["checkerPackIds"])])
        if config.get("ruleConfigFile"):
            cmd.extend(["--ruleConfigFile", config["ruleConfigFile"]])

        logger.info(f"Executing YASA: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        # YASA writes findings.sarif into report_dir
        sarif_file = report_dir / "findings.sarif"
        if not sarif_file.exists():
            # Try JSON fallback
            json_file = report_dir / "findings.json"
            if json_file.exists():
                sarif_file = json_file
            else:
                return {
                    "status": "error",
                    "error": f"YASA did not produce a report. Stderr: {result.stderr}",
                    "output": result.stdout,
                }

        # Rename to our timestamped filename for consistency with other tools
        final_path = report_dir.parent / f"{timestamp}.sarif"
        sarif_file.rename(final_path)

        # Count findings
        finding_count = 0
        try:
            with open(final_path) as f:
                data = json.load(f)
            for run in data.get("runs", []):
                finding_count += len(run.get("results", []))
        except Exception as e:
            logger.warning(f"Could not parse finding count: {e}")

        return {
            "status": "success",
            "finding_count": finding_count,
            "report_path": str(final_path),
            "timestamp": timestamp,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("YASA scan error")
        raise HTTPException(status_code=500, detail=str(e))
