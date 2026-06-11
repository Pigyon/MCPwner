import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from common.models import HealthResponse, ScanRequest, VersionResponse
from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)

app = FastAPI(title="Joern Service", version="1.0.0")

SCAN_SCRIPT = "/service/scan.sc"

# `joern --version` cold-starts the JVM (~16s). The health check hits /version
# on every tool at once, so an uncached call here regularly exceeds the client's
# 30s version timeout under load. Cache the result after the first resolution so
# subsequent health checks are instant.
_version_cache: dict = {"value": None}


def _resolve_version() -> str:
    if _version_cache["value"] is None:
        result = subprocess.run(
            ["joern", "--version"],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
        _version_cache["value"] = result.stdout.strip() or "unknown"
    return _version_cache["value"]


@app.on_event("startup")
def _warm_version_cache() -> None:
    """Resolve the JVM-backed version once at startup so the first health
    check doesn't pay the ~16s cold start. Runs in a background thread so it
    doesn't block uvicorn from serving /health immediately."""
    import threading

    def _warm():
        try:
            _resolve_version()
            logger.info(f"Joern version cached: {_version_cache['value']}")
        except Exception as e:
            logger.warning(f"Could not warm joern version cache at startup: {e}")

    threading.Thread(target=_warm, daemon=True).start()


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy", "service": "joern"}


@app.get("/version", response_model=VersionResponse)
def version():
    try:
        return {"version": _resolve_version(), "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan")
def scan(request: ScanRequest):
    try:
        full_scan_path = Path(request.workspace_path) / request.scan_path

        if not full_scan_path.exists():
            raise HTTPException(status_code=404, detail=f"Scan path does not exist: {full_scan_path}")

        # Build output path
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        parts = Path(request.workspace_path).parts
        if "workspaces" in parts:
            idx = parts.index("workspaces")
            if idx + 1 < len(parts):
                workspace_root = Path(*parts[: idx + 2])
                output_dir = workspace_root / "reports" / "sast" / "joern"
            else:
                output_dir = Path(request.workspace_path) / "reports" / "sast" / "joern"
        else:
            output_dir = Path(request.workspace_path).parent / "reports" / "sast" / "joern"

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}.json"

        config = request.config or {}

        # A hung tool must not block the request thread forever; bound it with a
        # timeout (10-minute default, overridable per-request).
        timeout_seconds = config.get("timeout_seconds", 600)

        # Determine scan mode: joern-scan (quick, uses query DB) or joern --script (custom)
        use_scan = config.get("mode", "script") == "scan"

        if use_scan:
            # Use joern-scan for automated scanning with the query database
            cmd = ["joern-scan", str(full_scan_path), "--overwrite"]

            if "tags" in config:
                cmd.extend(["--tags", config["tags"]])

            if "names" in config:
                cmd.extend(["--names", config["names"]])

            logger.info(f"Executing joern-scan: {' '.join(cmd)}")
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False, timeout=timeout_seconds
                )
            except subprocess.TimeoutExpired as e:
                logger.error(f"joern-scan timed out after {timeout_seconds}s")
                stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
                return {
                    "status": "error",
                    "error": f"Scan timed out after {timeout_seconds}s",
                    "output": stdout,
                }

            # Parse joern-scan text output into JSON
            findings = _parse_joern_scan_output(result.stdout)
            with open(output_path, "w") as f:
                json.dump(findings, f, indent=2)

            finding_count = len(findings)
        else:
            # Custom CPG analysis. Build the CPG up-front with joern-parse so we
            # can pass frontend-specific flags, then run the analysis script
            # against the prebuilt CPG. This is necessary because Joern's default
            # Java extraction runs delombok when a Lombok dependency is present
            # (e.g. WebGoat), and a delombok failure silently yields an EMPTY CPG
            # (0 methods/calls → 0 findings). Disabling delombok parses the raw
            # source directly and keeps all the security-relevant call sites.
            cpg_path = output_dir / f"{timestamp}.cpg.bin"

            parse_cmd = [
                "joern-parse",
                str(full_scan_path),
                "--output",
                str(cpg_path),
            ]
            # Only Java projects need the delombok override; passing
            # --delombok-mode to non-Java frontends would error.
            has_java = any(Path(full_scan_path).rglob("*.java"))
            if has_java:
                parse_cmd += ["--frontend-args", "--delombok-mode", "no-delombok"]

            logger.info(f"Building CPG: {' '.join(parse_cmd)}")
            try:
                parse_result = subprocess.run(
                    parse_cmd, capture_output=True, text=True, check=False, timeout=timeout_seconds
                )
            except subprocess.TimeoutExpired as e:
                logger.error(f"joern-parse timed out after {timeout_seconds}s")
                stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
                return {
                    "status": "error",
                    "error": f"CPG build timed out after {timeout_seconds}s",
                    "output": stdout,
                }

            if not cpg_path.exists():
                return {
                    "status": "error",
                    "error": f"Joern failed to build CPG. Stderr: {parse_result.stderr}",
                    "output": parse_result.stdout,
                }

            cmd = [
                "joern",
                "--script",
                SCAN_SCRIPT,
                "--param",
                f"cpgPath={cpg_path}",
                "--param",
                f"outFile={output_path}",
            ]

            logger.info(f"Executing joern script: {' '.join(cmd)}")
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False, timeout=timeout_seconds
                )
            except subprocess.TimeoutExpired as e:
                logger.error(f"joern script timed out after {timeout_seconds}s")
                stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
                return {
                    "status": "error",
                    "error": f"Scan timed out after {timeout_seconds}s",
                    "output": stdout,
                }

            if not output_path.exists():
                return {
                    "status": "error",
                    "error": f"Joern script failed to generate report. Stderr: {result.stderr}",
                    "output": result.stdout,
                }

            with open(output_path, "r") as f:
                data = json.load(f)
            finding_count = len(data) if isinstance(data, list) else 0

            # The intermediate CPG can be large; remove it so it doesn't get
            # picked up as a report or bloat the workspace volume.
            try:
                cpg_path.unlink(missing_ok=True)
            except OSError:
                pass

        return {
            "status": "success",
            "finding_count": finding_count,
            "report_path": str(output_path),
            "timestamp": timestamp,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Scan execution error")
        raise HTTPException(status_code=500, detail=str(e))


def _resolve_report_dir(workspace_path: str) -> Path:
    """Resolve the report directory for joern given a workspace path."""
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2]) / "reports" / "sast" / "joern"
    return Path(workspace_path).parent / "reports" / "sast" / "joern"


@app.get("/reports")
def list_reports(workspace_path: str):
    """List all available report timestamps for joern."""
    report_dir = _resolve_report_dir(workspace_path)
    if not report_dir.exists():
        return {"status": "success", "reports": []}
    reports = sorted(
        [f.stem for f in report_dir.iterdir() if f.is_file()],
        reverse=True,
    )
    return {"status": "success", "reports": reports}


@app.get("/report/{timestamp}")
def get_report(timestamp: str, workspace_path: str):
    """Retrieve the full contents of a joern scan report by its timestamp."""
    report_dir = _resolve_report_dir(workspace_path)
    for ext in ("json", "sarif"):
        candidate = report_dir / f"{timestamp}.{ext}"
        if candidate.exists():
            try:
                with open(candidate) as f:
                    data = json.load(f)
                return {"status": "success", "report": data, "report_path": str(candidate)}
            except json.JSONDecodeError:
                with open(candidate) as f:
                    raw = f.read()
                return {"status": "success", "report_raw": raw, "report_path": str(candidate)}
    raise HTTPException(
        status_code=404,
        detail=f"No report found for timestamp '{timestamp}' in {report_dir}",
    )


def _parse_joern_scan_output(output: str) -> list:
    """Parse joern-scan text output into structured JSON.

    joern-scan output format:
    Result: <score> : <title>: <filepath>:<line>:<function>
    """
    findings = []
    for line in output.strip().splitlines():
        line = line.strip()
        if not line.startswith("Result:"):
            continue
        try:
            # "Result: 8.0 : Dangerous function gets() used: /path/file.c:6:main"
            rest = line[len("Result:") :].strip()
            score_str, rest = rest.split(":", 1)
            score = float(score_str.strip())
            # rest = " Dangerous function gets() used: /path/file.c:6:main"
            # Split from the right to handle colons in the title
            parts = rest.rsplit(":", 3)
            if len(parts) >= 4:
                title_and_path = parts[0]
                # The last colon-separated segment before line:func is the filepath
                # title_and_path = " Dangerous function gets() used: /path/file.c"
                tp_parts = title_and_path.rsplit(":", 1)
                title = tp_parts[0].strip() if len(tp_parts) > 1 else title_and_path.strip()
                filepath = tp_parts[1].strip() if len(tp_parts) > 1 else ""
                line_number = parts[1].strip()
                function_name = parts[2].strip()
            else:
                title = rest.strip()
                filepath = ""
                line_number = ""
                function_name = ""

            findings.append(
                {
                    "score": score,
                    "title": title,
                    "filepath": filepath,
                    "line": line_number,
                    "function": function_name,
                }
            )
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse joern-scan line: {line}: {e}")
            continue

    return findings
