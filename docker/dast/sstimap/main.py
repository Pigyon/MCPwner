"""
SSTImap DAST service — SSTI scanner.

SSTImap outputs results to stdout with ANSI colors. The wrapper strips ANSI
codes and only reports confirmed injection indicators, filtering out negative
results and informational testing lines.

Config options:
  - target (required): URL with injectable parameter
  - data: POST body data
  - cookie: Cookie header
  - timeout_seconds: Scan timeout override (default 600)
"""

import re
import subprocess
from pathlib import Path

from common.dast_helpers import finding, strip_ansi, write_findings
from common.dast_service import create_dast_app
from common.models import ScanRequest

TOOL_NAME = "sstimap"
SSTIMAP_HOME = Path("/opt/sstimap")

_POSITIVE_RE = re.compile(
    r"\[\+\].*(?:injectable|confirmed|identified|exploitable)|"
    r"is injectable|"
    r"engine.*detected|"
    r"template engine:\s*\w+|"
    r"os shell|eval shell|tpl shell",
    re.IGNORECASE,
)

_NEGATIVE_RE = re.compile(
    r"not injectable|no injection|"
    r"\[\*\]\s*testing|"
    r"\[\*\]\s*loaded|"
    r"\[-\]\s*tested parameters appear|"
    r"\[\*\]\s*shutting down",
    re.IGNORECASE,
)


def _parse_sstimap_output(stdout: str, stderr: str, target: str) -> list:
    findings_list = []
    text = strip_ansi(f"{stdout}\n{stderr}")
    for line in text.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if _NEGATIVE_RE.search(line_stripped):
            continue
        if _POSITIVE_RE.search(line_stripped):
            findings_list.append(
                finding(
                    TOOL_NAME,
                    "SSTI confirmed",
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
    if not target:
        raise ValueError("target is required")

    cmd = ["python3", str(SSTIMAP_HOME / "sstimap.py"), "-u", target]
    if config.get("data"):
        cmd.extend(["--data", str(config["data"])])
    if config.get("cookie"):
        cmd.extend(["-C", str(config["cookie"])])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    write_findings(output_path, _parse_sstimap_output(result.stdout, result.stderr, target))


app = create_dast_app(
    TOOL_NAME,
    ["python3", str(SSTIMAP_HOME / "sstimap.py"), "-V"],
    execute_scan,
)
