"""
PoC-Script Sandbox Service

Runs an agent-authored, multi-step exploit script (stateful login -> act ->
assert) against a live target and reports a DETERMINISTIC oracle verdict. This
is the mechanism behind "no exploit, no report" for the vulnerability classes
that off-the-shelf DAST cannot prove: IDOR/BOLA (two-account differential),
broken access control (low-priv call to a privileged endpoint), race/TOCTOU
(concurrent requests), and multi-step business-logic / workflow bypass.

The security boundary is the CONTAINER, not this code: it runs unprivileged
(UID 1000, cap_drop ALL, no-new-privileges), resource-capped, with the script
confined to an exec tmpfs work dir and a minimal environment. It is only ever
attached to a target-reachable Docker network.

Config options (passed via ScanRequest.config):
  script:      Required. Source of the exploit script.
  interpreter: "python" (default) or "bash".
  target:      Optional. Exposed to the script as $TARGET and argv[1].
  env:         Optional dict of extra environment variables (str -> str), e.g.
               captured session cookies / tokens for authenticated testing.
  files:       Optional dict {relative_path: contents} of auxiliary files
               written next to the script before it runs.
  args:        Optional list of extra command-line arguments (after target).
  timeout:     Wall-clock seconds before the script is killed (default 120, max 600).

Oracle contract (deterministic — this is what makes a PoC "confirmed"):
  The script proves the exploit worked by exiting 0, and proves it failed by
  exiting non-zero. It MAY override the exit code by printing one of these on
  its own line:
      MCPWNER_ORACLE_PASS
      MCPWNER_ORACLE_FAIL
  and MAY attach structured evidence with:
      MCPWNER_ORACLE_JSON:{"...": "..."}
  A timed-out or non-launchable script never passes.
"""

import contextlib
import json
import logging
import os
import shlex
import shutil
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from tempfile import mkdtemp
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "poc-sandbox"
TOOL_CATEGORY = "poc"

# Keep stdout/stderr returned to the LLM bounded so a chatty script can't blow the context.
_MAX_STREAM_BYTES = 100 * 1024
# Hard ceiling on the caller-supplied timeout.
_MAX_TIMEOUT_SECONDS = 600
_DEFAULT_TIMEOUT_SECONDS = 120

_PASS_MARKER = "MCPWNER_ORACLE_PASS"  # noqa: S105
_FAIL_MARKER = "MCPWNER_ORACLE_FAIL"
_JSON_MARKER = "MCPWNER_ORACLE_JSON:"

app = FastAPI(title="PoC-Script Sandbox Service", version="1.0.0")


class ScanRequest(BaseModel):
    workspace_path: str
    scan_path: Optional[str] = "."
    config: Optional[Dict[str, Any]] = None
    report_base: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str


class VersionResponse(BaseModel):
    version: str
    status: str


def _report_dir(workspace_path: str, report_base: Optional[str] = None) -> Path:
    if report_base:
        return Path(report_base) / "reports" / TOOL_CATEGORY / TOOL_NAME
    parts = Path(workspace_path).parts
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        if idx + 1 < len(parts):
            return Path(*parts[: idx + 2]) / "reports" / TOOL_CATEGORY / TOOL_NAME
    return Path(workspace_path).parent / "reports" / TOOL_CATEGORY / TOOL_NAME


def _truncate(text: str) -> str:
    encoded = text.encode("utf-8", "replace")
    if len(encoded) <= _MAX_STREAM_BYTES:
        return text
    return encoded[:_MAX_STREAM_BYTES].decode("utf-8", "ignore") + "\n...[truncated]"


def _build_env(user_env: Dict[str, Any], target: str, workdir: str) -> Dict[str, str]:
    """Minimal, non-inherited environment so the parent's vars don't leak into the PoC."""
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": workdir,
        "LANG": "C.UTF-8",
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if target:
        env["TARGET"] = target
    for key, value in (user_env or {}).items():
        # Only accept scalar values; coerce to str so requests headers etc. behave.
        if isinstance(value, (str, int, float, bool)):
            env[str(key)] = str(value)
    return env


def _parse_oracle(stdout: str, exit_code: int, timed_out: bool) -> Dict[str, Any]:
    """Deterministic verdict: explicit marker wins, else exit code; timeout never passes."""
    marker_json: Optional[Dict[str, Any]] = None
    explicit: Optional[bool] = None
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped == _PASS_MARKER:
            explicit = True
        elif stripped == _FAIL_MARKER:
            explicit = False
        elif stripped.startswith(_JSON_MARKER):
            try:
                marker_json = json.loads(stripped[len(_JSON_MARKER) :].strip())
            except (json.JSONDecodeError, ValueError):
                marker_json = {"parse_error": stripped[len(_JSON_MARKER) :][:500]}

    if timed_out:
        passed = False
    elif explicit is not None:
        passed = explicit
    else:
        passed = exit_code == 0

    return {
        "kind": "poc-script",
        "passed": passed,
        "decided_by": "timeout" if timed_out else ("marker" if explicit is not None else "exit_code"),
        "evidence": marker_json,
    }


def _run_script(
    script: str,
    interpreter: str,
    target: str,
    user_env: Dict[str, Any],
    files: Dict[str, Any],
    extra_args: List[str],
    timeout_s: int,
) -> Dict[str, Any]:
    workdir = mkdtemp(prefix="poc_", dir="/tmp")
    try:
        return _run_script_in(
            workdir, script, interpreter, target, user_env, files, extra_args, timeout_s
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _run_script_in(
    workdir: str,
    script: str,
    interpreter: str,
    target: str,
    user_env: Dict[str, Any],
    files: Dict[str, Any],
    extra_args: List[str],
    timeout_s: int,
) -> Dict[str, Any]:
    if interpreter == "bash":
        script_name = "exploit.sh"
        cmd = ["bash", script_name]
    else:
        interpreter = "python"
        script_name = "exploit.py"
        cmd = ["python3", script_name]

    (Path(workdir) / script_name).write_text(script, encoding="utf-8")

    for rel_path, contents in (files or {}).items():
        # Confine auxiliary files to the work dir; reject traversal.
        dest = (Path(workdir) / rel_path).resolve()
        if not str(dest).startswith(str(Path(workdir).resolve()) + os.sep):
            raise HTTPException(status_code=400, detail=f"Illegal file path in files: {rel_path}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = contents if isinstance(contents, str) else json.dumps(contents)
        dest.write_text(text, encoding="utf-8")

    argv = cmd + ([target] if target else []) + [str(a) for a in (extra_args or [])]
    env = _build_env(user_env, target, workdir)

    start = time.time()
    timed_out = False
    try:
        # start_new_session so a wedged child (and anything it spawns) can be killed as a group.
        proc = subprocess.Popen(
            argv,
            cwd=workdir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            text=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout_s)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            with contextlib.suppress(Exception):
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.stdout.read() or "", proc.stderr.read() or ""
            exit_code = -signal.SIGKILL
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"Interpreter not available: {e}")
    duration = round(time.time() - start, 2)

    stdout = _truncate(stdout or "")
    stderr = _truncate(stderr or "")
    oracle = _parse_oracle(stdout, exit_code, timed_out)

    rerun = (
        f"run_poc_scan(tool='poc-sandbox', target={target!r}, "
        f"config={{'interpreter': {interpreter!r}, 'script': <the same script>}})"
    )

    return {
        "interpreter": interpreter,
        "command": " ".join(shlex.quote(a) for a in argv),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_seconds": duration,
        "stdout": stdout,
        "stderr": stderr,
        "oracle": oracle,
        "script": script,
        "rerun_command": rerun,
    }


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy", "service": TOOL_NAME}


@app.get("/version", response_model=VersionResponse)
def version():
    import platform

    return {"version": f"python {platform.python_version()}", "status": "success"}


@app.post("/scan")
def scan(request: ScanRequest):
    """Execute an agent-authored PoC script against the target and return the oracle verdict."""
    try:
        cfg = request.config or {}
        script = cfg.get("script")
        if not script or not isinstance(script, str):
            raise HTTPException(status_code=400, detail="config.script (a source string) is required")

        interpreter = str(cfg.get("interpreter", "python")).lower()
        if interpreter not in ("python", "bash"):
            raise HTTPException(status_code=400, detail="config.interpreter must be 'python' or 'bash'")

        target = str(cfg.get("target", "") or "")
        user_env = cfg.get("env") or {}
        files = cfg.get("files") or {}
        extra_args = cfg.get("args") or []
        timeout_s = min(int(cfg.get("timeout", _DEFAULT_TIMEOUT_SECONDS)), _MAX_TIMEOUT_SECONDS)
        timeout_s = max(1, timeout_s)

        logger.info(f"Running {interpreter} PoC (timeout {timeout_s}s), target={target or 'none'}")
        run = _run_script(script, interpreter, target, user_env, files, extra_args, timeout_s)

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        output_dir = _report_dir(request.workspace_path, request.report_base)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}.json"

        report = {"target": target, **run}
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return {
            "status": "success",
            "finding_count": 1 if run["oracle"]["passed"] else 0,
            "report_path": str(output_path),
            "timestamp": timestamp,
            "oracle_passed": run["oracle"]["passed"],
            "oracle_decided_by": run["oracle"]["decided_by"],
            "exit_code": run["exit_code"],
            "timed_out": run["timed_out"],
            "duration_seconds": run["duration_seconds"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("PoC sandbox error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports")
def list_reports(workspace_path: str, report_base: str = None):
    report_dir = _report_dir(workspace_path, report_base)
    if not report_dir.exists():
        return {"status": "success", "reports": []}
    reports = sorted([f.stem for f in report_dir.iterdir() if f.is_file()], reverse=True)
    return {"status": "success", "reports": reports}


@app.get("/report/{timestamp}")
def get_report(timestamp: str, workspace_path: str, report_base: str = None):
    report_dir = _report_dir(workspace_path, report_base)
    candidate = report_dir / f"{timestamp}.json"
    if not candidate.exists():
        raise HTTPException(status_code=404, detail=f"No report for timestamp '{timestamp}'")
    with open(candidate) as f:
        data = json.load(f)
    return {"status": "success", "report": data, "report_path": str(candidate)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8134))
    uvicorn.run(app, host="0.0.0.0", port=port)
