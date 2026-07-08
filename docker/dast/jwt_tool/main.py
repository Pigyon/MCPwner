"""
jwt_tool DAST service — JWT vulnerability scanner.

jwt_tool requires the JWT as a positional argument and the target URL via -t.
To inject the token into the HTTP request, the wrapper passes it as a cookie
(-rc) in the Authorization header so jwt_tool can actually replay modified
tokens against the target.

Config options:
  - target (required): URL to send forged JWT requests to
  - token (required): JWT token string
  - mode: Scan mode (default: pb = playbook audit)
  - cookie_name: Cookie name for token injection (default: token)
  - timeout_seconds: Scan timeout override (default 600)
"""

import re
import subprocess
from pathlib import Path

from common.dast_helpers import finding, strip_ansi, write_findings
from common.dast_service import create_dast_app
from common.models import ScanRequest

TOOL_NAME = "jwt_tool"
JWT_TOOL_HOME = Path("/opt/jwt_tool")

_POSITIVE_RE = re.compile(
    r"\[\+\].*(?:vulnerable|crack|exploit|weak|bypass|forged|accepted|"
    r"response code.*200|valid|none|null signature|blank password)|"
    r"jwttool_\w+.*response",
    re.IGNORECASE,
)

_INFORMATIONAL_RE = re.compile(
    r"\[\+\]\s*(?:alg|typ|sub|iat|exp|nbf|iss|aud|jti)\s*=|"
    r"original jwt|decoded token|common timestamps|"
    r"version \d|@ticarpi|"
    r"^\s*$",
    re.IGNORECASE,
)


def _parse_jwt_output(stdout: str, stderr: str, target: str) -> list:
    findings_list = []
    text = strip_ansi(f"{stdout}\n{stderr}")
    for line in text.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if _INFORMATIONAL_RE.search(line_stripped):
            continue
        if _POSITIVE_RE.search(line_stripped):
            severity = (
                "high"
                if re.search(r"vulnerable|exploit|crack|weak|bypass", line_stripped, re.IGNORECASE)
                else "medium"
            )
            findings_list.append(
                finding(
                    TOOL_NAME,
                    "JWT vulnerability",
                    severity,
                    target=target,
                    detail=line_stripped,
                    evidence=line_stripped,
                )
            )

    if not findings_list:
        for line in text.splitlines():
            line_stripped = line.strip()
            if re.search(r"\[-\].*(?:no|not|failed|rejected|error)", line_stripped, re.IGNORECASE):
                continue
            if re.search(r"jwttool_\w+", line_stripped):
                findings_list.append(
                    finding(
                        TOOL_NAME,
                        "JWT test attempt",
                        "info",
                        target=target,
                        detail=line_stripped,
                        evidence=line_stripped,
                    )
                )
    return findings_list


def execute_scan(request: ScanRequest, output_path: Path, timeout_seconds: int) -> None:
    config = request.config or {}
    target = str(config.get("target", "")).strip()
    token = str(config.get("token", "")).strip()
    if not target:
        raise ValueError("target is required")
    if not token:
        raise ValueError("token is required")

    mode = str(config.get("mode", "pb")).strip()
    cookie_name = str(config.get("cookie_name", "token")).strip()

    cmd = [
        "python3",
        str(JWT_TOOL_HOME / "jwt_tool.py"),
        token,
        "-t",
        target,
        "-rh",
        f"Authorization: Bearer {token}",
        "-M",
        mode,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    write_findings(output_path, _parse_jwt_output(result.stdout, result.stderr, target))


app = create_dast_app(
    TOOL_NAME,
    ["python3", str(JWT_TOOL_HOME / "jwt_tool.py"), "-h"],
    execute_scan,
)
