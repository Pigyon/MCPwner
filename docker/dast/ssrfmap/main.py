"""
SSRFmap DAST service — SSRF exploitation framework.

SSRFmap requires a raw HTTP request file with an injectable parameter.
The wrapper parses stdout for confirmed exploitation results, filtering out
operational log lines.

Config options:
  - target (optional): URL context
  - raw_request (required): Raw HTTP request text with the SSRF parameter
  - param (required): Name of the parameter to inject into
  - module: SSRFmap module (default: readfiles)
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

TOOL_NAME = "ssrfmap"
SSRFMAP_HOME = Path("/opt/ssrfmap")

_OPERATIONAL_RE = re.compile(
    r"^\[INFO\]\s*(Log file|Module .+ launched|Testing|Starting|$)|"
    r"^_+\s*$|"
    r"^/\s*|"
    r"SSRFmap|projectdiscovery|usage:",
    re.IGNORECASE,
)

_POSITIVE_RE = re.compile(
    r"root:|www-data:|/etc/passwd|"
    r"successfully|"
    r"\[\+\]|"
    r"SSRF.*confirmed|"
    r"retrieved|"
    r"response.*200|"
    r"data:|content:",
    re.IGNORECASE,
)


def _parse_ssrfmap_output(stdout: str, stderr: str, target: str) -> list:
    findings_list = []
    text = strip_ansi(f"{stdout}\n{stderr}")
    for line in text.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if _OPERATIONAL_RE.search(line_stripped):
            continue
        if _POSITIVE_RE.search(line_stripped):
            findings_list.append(
                finding(
                    TOOL_NAME,
                    "SSRF exploitation result",
                    "high",
                    target=target,
                    detail=line_stripped,
                    evidence=line_stripped,
                )
            )
    return findings_list


def execute_scan(request: ScanRequest, output_path: Path, timeout_seconds: int) -> None:
    config = request.config or {}
    target = str(config.get("target", "")).strip()
    raw_request = str(config.get("raw_request", "")).strip()
    param = str(config.get("param", "url")).strip()
    module = str(config.get("module", "readfiles")).strip()

    if not raw_request:
        raise ValueError("raw_request is required for SSRFmap (raw HTTP request text)")

    workspace_root = resolve_workspace_root(request.workspace_path)
    work_dir = scan_work_dir(workspace_root, TOOL_NAME)
    request_file = write_raw_request(raw_request, work_dir)

    cmd = [
        "python3",
        str(SSRFMAP_HOME / "ssrfmap.py"),
        "-r",
        str(request_file),
        "-p",
        param,
        "-m",
        module,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    write_findings(
        output_path,
        _parse_ssrfmap_output(result.stdout, result.stderr, target or "raw_request"),
    )


app = create_dast_app(
    TOOL_NAME,
    ["python3", str(SSRFMAP_HOME / "ssrfmap.py"), "-h"],
    execute_scan,
)
