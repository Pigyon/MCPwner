"""
Commix DAST service — command injection exploitation.

Commix writes session logs to its output directory. The wrapper parses both
stdout and log files, filtering out banner/operational lines so only confirmed
injection evidence is reported.

Config options:
  - target (required): URL to test for command injection
  - data: POST body data (e.g. "ip=127.0.0.1&Submit=Submit")
  - cookie: Cookie header (e.g. "PHPSESSID=abc; security=low")
  - timeout_seconds: Scan timeout override (default 600)
"""

import re
import subprocess
from pathlib import Path

from common.dast_helpers import (
    finding,
    resolve_workspace_root,
    scan_work_dir,
    strip_ansi,
    write_findings,
)
from common.dast_service import create_dast_app
from common.models import ScanRequest

TOOL_NAME = "commix"
COMMIX_HOME = Path("/opt/commix")

_BANNER_RE = re.compile(
    r"automated all-in-one|commix v\d|os command injection|"
    r"legal disclaimer|testing connection|retrieving|starting|ending @|"
    r"total of \d+ unique results",
    re.IGNORECASE,
)

_POSITIVE_RE = re.compile(
    r"the (?:GET|POST|COOKIE|HEADER) parameter .+ (?:is|appears to be) injectable|"
    r"command execution output|"
    r"the remote host is|"
    r"identified the following injection point|"
    r"available techniques|"
    r"\(results-based\)|"
    r"\(time-based\)|"
    r"\(file-based\)|"
    r"\[info\]\s*type:\s*.*command injection|"
    r"\[info\]\s*technique:\s*|"
    r"\[info\]\s*parameter:\s*",
    re.IGNORECASE,
)


def _parse_commix_output(stdout: str, stderr: str, output_dir: Path) -> list:
    findings_list = []
    text = strip_ansi(f"{stdout}\n{stderr}")

    for line in text.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if _BANNER_RE.search(line_stripped):
            continue
        if _POSITIVE_RE.search(line_stripped):
            findings_list.append(
                finding(
                    TOOL_NAME,
                    "Command injection confirmed",
                    "high",
                    detail=line_stripped,
                    evidence=line_stripped,
                )
            )

    for log_file in output_dir.rglob("*.txt"):
        try:
            content = log_file.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                line_stripped = strip_ansi(line.strip())
                if _POSITIVE_RE.search(line_stripped) and not _BANNER_RE.search(line_stripped):
                    findings_list.append(
                        finding(
                            TOOL_NAME,
                            "Command injection (session log)",
                            "high",
                            detail=line_stripped,
                            evidence=str(log_file),
                        )
                    )
        except OSError:
            continue
    return findings_list


def execute_scan(request: ScanRequest, output_path: Path, timeout_seconds: int) -> None:
    config = request.config or {}
    target = str(config.get("target", "")).strip()
    if not target:
        raise ValueError("target is required")

    workspace_root = resolve_workspace_root(request.workspace_path)
    work_dir = scan_work_dir(workspace_root, TOOL_NAME)
    tool_out = work_dir / "output"
    tool_out.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python3",
        str(COMMIX_HOME / "commix.py"),
        "--batch",
        "--ignore-stdin",
        f"--output-dir={tool_out}",
        "-u",
        target,
    ]
    if config.get("data"):
        cmd.extend(["--data", str(config["data"])])
    if config.get("cookie"):
        cmd.extend(["--cookie", str(config["cookie"])])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout, stderr = result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    write_findings(output_path, _parse_commix_output(stdout, stderr, tool_out))


app = create_dast_app(
    TOOL_NAME,
    ["python3", str(COMMIX_HOME / "commix.py"), "--version"],
    execute_scan,
)
