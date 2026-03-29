import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from common.models import HealthResponse, ScanRequest, VersionResponse
from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)

app = FastAPI(title="YASA Service", version="1.0.0")

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

_SUPPORTED = set(_LANG_MAP.keys())

# File-extension based auto-detection for when no language is specified
_EXT_TO_LANG = {
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "javascript",
    ".tsx": "javascript",
    ".jsx": "javascript",
    ".go": "golang",
    ".java": "java",
    ".py": "python",
}


def _detect_language(source_path: Path) -> str:
    """Detect dominant language from file extensions in source directory."""
    counts: dict[str, int] = {}
    for f in source_path.rglob("*"):
        if f.is_file() and "node_modules" not in f.parts and ".git" not in f.parts:
            lang = _EXT_TO_LANG.get(f.suffix.lower())
            if lang:
                counts[lang] = counts.get(lang, 0) + 1
    if not counts:
        return "javascript"  # safe default
    return max(counts, key=counts.get)


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy", "service": "yasa"}


@app.get("/version", response_model=VersionResponse)
def version():
    try:
        result = subprocess.run(
            ["yasa", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
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

        # Build command — YASA requires --language or --analyzer
        cmd = [
            "yasa",
            "--sourcePath",
            str(full_scan_path),
            "--report",
            str(report_dir),
        ]

        # Language: explicit config > auto-detect from source files
        lang = config.get("language", "")
        if lang:
            mapped = _LANG_MAP.get(lang.lower())
            if not mapped:
                return {
                    "status": "error",
                    "error": (
                        f"Unsupported language '{lang}'. Supported: {', '.join(sorted(_SUPPORTED))}"
                    ),
                }
        else:
            # Auto-detect from source directory
            mapped = _detect_language(full_scan_path)
            logger.info(f"Auto-detected language: {mapped}")

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

        # YASA writes its report into report_dir; find whatever file it created
        sarif_file = report_dir / "findings.sarif"
        if not sarif_file.exists():
            for candidate in report_dir.iterdir():
                if candidate.is_file():
                    sarif_file = candidate
                    break
            else:
                return {
                    "status": "error",
                    "error": f"YASA did not produce a report. Stderr: {result.stderr}",
                    "output": result.stdout,
                }

        # Rename to timestamped filename, preserving extension
        final_path = report_dir.parent / f"{timestamp}{sarif_file.suffix}"
        sarif_file.rename(final_path)

        # Count findings — YASA may output NDJSON (one object per line) or a JSON array/object
        finding_count = 0
        try:
            with open(final_path) as f:
                raw = f.read().strip()
            # Try standard JSON first
            try:
                data = json.loads(raw)
                if isinstance(data, list):
                    finding_count = len(data)
                elif isinstance(data, dict):
                    for run in data.get("runs", []):
                        finding_count += len(run.get("results", []))
            except json.JSONDecodeError:
                # NDJSON fallback — count non-empty lines that are valid JSON
                lines = [ln for ln in raw.splitlines() if ln.strip()]
                finding_count = sum(1 for ln in lines if ln.strip().startswith("{"))
                # Rewrite as JSON array for consistent downstream consumption
                parsed = [json.loads(ln) for ln in lines if ln.strip()]
                with open(final_path, "w") as f:
                    json.dump(parsed, f, indent=2)
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
