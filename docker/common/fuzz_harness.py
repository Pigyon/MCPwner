#!/usr/bin/env python3
"""Shared source-fuzzing runner used by every fuzzing engine container.

The fuzzing engines MCPwner integrates (Atheris, Jazzer, Jazzer.js, PHP-Fuzzer)
are all coverage-guided, libFuzzer-style fuzzers driven by a small per-target
*harness* that lives in the workspace source tree. They do not, on their own,
emit a machine-readable report — they run until they find a crashing input (or
the time budget expires), drop the crashing bytes into an *artifact* file, and
print a stack trace.

``create_scanner_app`` (the shared FastAPI factory) expects a tool to run one
command that leaves a report file at ``--out``. This runner is that command: it
builds the engine invocation from the request config, bounds it with a
wall-clock timeout, collects any crash artifacts, parses the engine's output for
a crash signature and execution count, and writes a single JSON report that the
factory then surfaces (one finding per crash artifact).

It is deliberately dependency-free (stdlib only) so it can run unchanged under
the system Python of every engine image, regardless of how that image installs
its FastAPI service.
"""

import argparse
import base64
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Crash artifacts libFuzzer-style engines (and php-fuzzer) drop on a finding.
_ARTIFACT_GLOBS = ("crash-*", "leak-*", "oom-*", "timeout-*", "slow-unit-*")

# Output lines that signal a crash even when no artifact file was written.
_CRASH_MARKERS = (
    "uncaught python exception",
    "== java exception",
    "uncaught exception",
    "== libfuzzer crashing input",
    "deduplication token",
    "fatalerror",
    "fuzz target exited",
    "==error",
    "fuzzer crashed",
    "the input that triggered",
    # php-fuzzer crash output (0.0.11 writes "CRASH in <file>!" during fuzz and
    # "CORPUS CRASH in <file>!" when a seeded input crashes on load).
    "crash in ",
    "corpus crash",
)

# How long to keep reading the engine after its time budget before hard-killing.
_DEFAULT_GRACE_SECONDS = 30
_LOG_TAIL_LINES = 120


def _resolve(base: Path, rel: Optional[str]) -> Optional[Path]:
    """Resolve a workspace-relative path against the scan base directory."""
    if not rel:
        return None
    p = Path(rel)
    return p if p.is_absolute() else (base / p)


def _classpath_arg(base: Path, classpath: Any) -> str:
    """Build a JVM classpath string from a list or ':'-separated config value."""
    parts = list(classpath) if isinstance(classpath, (list, tuple)) else str(classpath).split(":")
    resolved = [str(_resolve(base, part.strip())) for part in parts if part.strip()]
    return ":".join(resolved)


def _engine_args(config: Dict[str, Any]) -> List[str]:
    extra = config.get("engine_args") or []
    return [str(a) for a in extra]


def build_command(
    engine: str,
    base: Path,
    config: Dict[str, Any],
    artifact_dir: Path,
    max_total_time: int,
) -> Dict[str, Any]:
    """Return {cmd, cwd, env} for the requested engine.

    Raises ValueError for missing required config so the caller can report a
    clear configuration error rather than a cryptic engine failure.
    """
    runs = config.get("runs")
    corpus = _resolve(base, config.get("corpus"))
    artifact_prefix = f"-artifact_prefix={artifact_dir}/"
    env = dict(os.environ)

    if engine == "atheris":
        harness = _resolve(base, config.get("harness"))
        if not harness:
            raise ValueError("config.harness is required for atheris")
        cmd = [
            sys.executable,
            str(harness),
            artifact_prefix,
            f"-max_total_time={max_total_time}",
        ]
        if runs is not None:
            cmd.append(f"-runs={int(runs)}")
        cmd += _engine_args(config)
        if corpus:
            cmd.append(str(corpus))
        # Let the harness import the target module from the source tree.
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(base), str(harness.parent), existing]))
        return {"cmd": cmd, "cwd": str(base), "env": env}

    if engine == "jazzer":
        target_class = config.get("target_class")
        if not target_class:
            raise ValueError("config.target_class is required for jazzer")
        if not config.get("classpath"):
            raise ValueError("config.classpath is required for jazzer (compiled classes/jars)")
        cmd = [
            "jazzer",
            f"--cp={_classpath_arg(base, config['classpath'])}",
            f"--target_class={target_class}",
            artifact_prefix,
            f"-max_total_time={max_total_time}",
        ]
        if runs is not None:
            cmd.append(f"-runs={int(runs)}")
        cmd += _engine_args(config)
        if corpus:
            cmd.append(str(corpus))
        return {"cmd": cmd, "cwd": str(base), "env": env}

    if engine == "jazzerjs":
        harness = _resolve(base, config.get("harness"))
        if not harness:
            raise ValueError("config.harness is required for jazzerjs")
        cmd = ["jazzer", str(harness)]
        if corpus:
            cmd.append(str(corpus))
        # libFuzzer args go after '--'.
        cmd += ["--", artifact_prefix, f"-max_total_time={max_total_time}"]
        if runs is not None:
            cmd.append(f"-runs={int(runs)}")
        cmd += _engine_args(config)
        return {"cmd": cmd, "cwd": str(base), "env": env}

    if engine == "php-fuzzer":
        harness = _resolve(base, config.get("harness"))
        if not harness:
            raise ValueError("config.harness is required for php-fuzzer")
        # php-fuzzer 0.0.11 has no --max-total-time flag; the wall-clock timeout
        # bounds it. Crash files are written to the process CWD, so run inside
        # artifact_dir so _collect_artifacts finds them. The corpus arg is also
        # artifact_dir (php-fuzzer creates it if absent); pass a user corpus when
        # provided so seeds are loaded before fuzzing starts.
        corpus_dir = str(corpus) if corpus else str(artifact_dir)
        cmd = ["php-fuzzer", "fuzz", str(harness), corpus_dir]
        cmd += _engine_args(config)
        return {"cmd": cmd, "cwd": str(artifact_dir), "env": env}

    raise ValueError(f"Unknown fuzzing engine: {engine}")


def _collect_artifacts(*dirs: Path) -> List[Path]:
    found: List[Path] = []
    seen = set()
    for d in dirs:
        for pattern in _ARTIFACT_GLOBS:
            for match in glob.glob(str(d / pattern)):
                if match not in seen and Path(match).is_file():
                    seen.add(match)
                    found.append(Path(match))
    return found


def _tail(text: str, lines: int = _LOG_TAIL_LINES) -> str:
    rows = text.splitlines()
    return "\n".join(rows[-lines:])


def _executions(output: str) -> Optional[int]:
    """Best-effort parse of the number of executed inputs from engine output."""
    m = re.search(r"stat::number_of_executed_units:\s*(\d+)", output)
    if m:
        return int(m.group(1))
    counts = re.findall(r"^#(\d+)\s", output, re.MULTILINE)
    if counts:
        return int(counts[-1])
    return None


def _crash_signature(output: str) -> str:
    """Extract a short, human-readable crash signature from engine output."""
    patterns = [
        r"(== Java Exception:.*)",
        r"(Uncaught Python exception.*)",
        r"(==\d+==ERROR:.*)",
        r"(SUMMARY:.*)",
        r"(Uncaught .*Error.*)",
    ]
    for pat in patterns:
        m = re.search(pat, output)
        if m:
            return m.group(1).strip()[:300]
    return ""


def _input_fields(artifact: Path) -> Dict[str, Any]:
    try:
        raw = artifact.read_bytes()
    except OSError:
        return {"input_base64": None, "input_preview": None}
    preview = raw[:200].decode("utf-8", "replace")
    return {
        "input_base64": base64.b64encode(raw).decode("ascii"),
        "input_size": len(raw),
        "input_preview": preview,
    }


def run(engine: str, base: Path, out_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    max_total_time = int(config.get("max_total_time", 60))
    grace = int(config.get("grace_seconds", _DEFAULT_GRACE_SECONDS))
    # libFuzzer engines (atheris, jazzer, jazzerjs) self-terminate at
    # max_total_time; the grace period lets them finish writing crash artifacts.
    # php-fuzzer has no built-in time limit and is killed by us, so no grace.
    wall_timeout = max_total_time if engine == "php-fuzzer" else max_total_time + grace

    artifact_dir = Path(tempfile.mkdtemp(prefix="fuzz-artifacts-"))

    report: Dict[str, Any] = {
        "tool": engine,
        "engine": engine,
        "status": "success",
        "crash_found": False,
        "max_total_time": max_total_time,
        "results": [],
    }

    try:
        spec = build_command(engine, base, config, artifact_dir, max_total_time)
    except ValueError as e:
        # Configuration error — surface it but still emit a parseable report.
        report["status"] = "error"
        report["error"] = str(e)
        return report

    report["command"] = " ".join(spec["cmd"])
    started = time.time()
    timed_out = False
    stdout = ""
    stderr = ""
    exit_code: Optional[int] = None

    try:
        proc = subprocess.run(
            spec["cmd"],
            cwd=spec["cwd"],
            env=spec["env"],
            capture_output=True,
            text=True,
            timeout=wall_timeout,
            check=False,
        )
        stdout, stderr = proc.stdout or "", proc.stderr or ""
        exit_code = proc.returncode
    except subprocess.TimeoutExpired as e:
        timed_out = True
        stdout = (e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout) or ""
        stderr = (e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr) or ""
    except FileNotFoundError as e:
        report["status"] = "error"
        report["error"] = f"Fuzzing engine binary not found: {e}"
        return report

    duration = round(time.time() - started, 1)
    combined = f"{stdout}\n{stderr}"

    artifacts = _collect_artifacts(artifact_dir, Path(spec["cwd"]))

    # php-fuzzer names crash files after their MD5 hash without a "crash-" prefix
    # when CWD == corpus dir, so the glob above misses them.  Parse "CRASH in
    # <path>!" / "CORPUS CRASH in <path>!" lines to grab the exact file path.
    if engine == "php-fuzzer":
        for m in re.finditer(r"(?:CORPUS )?CRASH in (.+?)!", combined):
            p = Path(m.group(1).strip())
            if p.is_file() and p not in artifacts:
                artifacts.append(p)

    lowered = combined.lower()
    crash_by_marker = any(marker in lowered for marker in _CRASH_MARKERS)
    # libFuzzer engines exit non-zero on a finding; a clean timeout (php-fuzzer
    # hitting the budget) is not itself a crash.
    crash_by_exit = exit_code not in (0, None) and not timed_out

    crash_found = bool(artifacts) or crash_by_marker or crash_by_exit
    signature = _crash_signature(combined)

    results: List[Dict[str, Any]] = []
    for artifact in artifacts:
        entry = {
            "ruleId": "fuzzing/crash",
            "engine": engine,
            "crash_type": signature or "crash",
            "message": signature or f"{engine} produced a crashing input",
            "artifact": artifact.name,
            "stack_trace": _tail(combined, 60),
        }
        entry.update(_input_fields(artifact))
        results.append(entry)

    if crash_found and not results:
        # Crash detected from output/exit code but no artifact file was captured.
        results.append(
            {
                "ruleId": "fuzzing/crash",
                "engine": engine,
                "crash_type": signature or "crash",
                "message": signature or f"{engine} reported a crash (no artifact file captured)",
                "artifact": None,
                "input_base64": None,
                "stack_trace": _tail(combined, 60),
            }
        )

    report.update(
        {
            "crash_found": crash_found,
            "results": results,
            "executions": _executions(combined),
            "duration_seconds": duration,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "log_tail": _tail(combined),
        }
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="MCPwner source-fuzzing runner")
    parser.add_argument("--engine", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--scan-path", default=".")
    parser.add_argument("--out", required=True)
    parser.add_argument("--config", default="{}", help="JSON-encoded engine config")
    args = parser.parse_args()

    try:
        config = json.loads(args.config) if args.config else {}
        if not isinstance(config, dict):
            config = {}
    except json.JSONDecodeError:
        config = {}

    base = (Path(args.workspace) / (args.scan_path or ".")).resolve()
    out_path = Path(args.out)

    try:
        report = run(args.engine, base, out_path, config)
    except Exception as e:  # never crash without leaving a report
        report = {
            "tool": args.engine,
            "engine": args.engine,
            "status": "error",
            "crash_found": False,
            "error": f"fuzz runner failed: {e}",
            "results": [],
        }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    # Always exit 0: the report file is the contract. The factory parses it for
    # the finding (crash) count regardless of the engine's own exit code.
    return 0


if __name__ == "__main__":
    sys.exit(main())
