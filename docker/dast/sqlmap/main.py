"""
SQLMap DAST service — SQL injection scanner.

sqlmap writes results to stdout and session files. The wrapper parses both
stdout and the session output directory to extract confirmed injection findings.

Config options:
  - target (required unless raw_request): URL with injectable parameter
  - raw_request: Raw HTTP request text (fed via -r flag)
  - data: POST body data
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
    write_raw_request,
)
from common.dast_service import create_dast_app
from common.models import ScanRequest

TOOL_NAME = "sqlmap"


def _parse_sqlmap_output(stdout: str, stderr: str) -> list:
    text = strip_ansi(f"{stdout}\n{stderr}")
    findings = []

    if re.search(r"unable to connect|Connection refused|connection timed out", text, re.IGNORECASE):
        findings.append(
            finding(
                TOOL_NAME,
                "Target unreachable",
                "info",
                detail="sqlmap could not connect to the target URL",
            )
        )
        return findings

    for match in re.finditer(
        r"Parameter:\s*[#']?(\S+?)[#']?\s+\((.*?)\)\s*$",
        text,
        re.MULTILINE,
    ):
        param, injection_type = match.group(1), match.group(2)
        findings.append(
            finding(
                TOOL_NAME,
                f"SQL injection in '{param}'",
                "high",
                detail=f"Type: {injection_type}",
                evidence=match.group(0).strip(),
            )
        )

    for match in re.finditer(
        r"Type:\s*(.*?)\s*Title:\s*(.*?)\s*Payload:\s*(.*?)$",
        text,
        re.MULTILINE,
    ):
        findings.append(
            finding(
                TOOL_NAME,
                match.group(2).strip(),
                "high",
                detail=f"Type: {match.group(1).strip()}",
                evidence=f"Payload: {match.group(3).strip()}",
            )
        )

    if not findings and re.search(r"is vulnerable|injection point", text, re.IGNORECASE):
        for line in text.splitlines():
            if re.search(r"is vulnerable|injection point", line, re.IGNORECASE):
                findings.append(
                    finding(
                        TOOL_NAME,
                        "SQL injection detected",
                        "high",
                        detail=line.strip(),
                        evidence=line.strip(),
                    )
                )
                break

    return findings


def execute_scan(request: ScanRequest, output_path: Path, timeout_seconds: int) -> None:
    config = request.config or {}
    target = str(config.get("target", "")).strip()
    raw_request = str(config.get("raw_request", "")).strip()
    if not target and not raw_request:
        raise ValueError("target or raw_request is required")

    workspace_root = resolve_workspace_root(request.workspace_path)
    work_dir = scan_work_dir(workspace_root, TOOL_NAME)
    tool_out = work_dir / "output"
    tool_out.mkdir(parents=True, exist_ok=True)

    cmd = ["sqlmap", "--batch", f"--output-dir={tool_out}"]
    if raw_request:
        cmd.extend(["-r", str(write_raw_request(raw_request, work_dir))])
    else:
        cmd.extend(["-u", target])
    if config.get("data"):
        cmd.extend(["--data", str(config["data"])])
    if config.get("cookie"):
        cmd.extend(["--cookie", str(config["cookie"])])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    write_findings(output_path, _parse_sqlmap_output(result.stdout, result.stderr))


app = create_dast_app(TOOL_NAME, ["sqlmap", "--version"], execute_scan)
