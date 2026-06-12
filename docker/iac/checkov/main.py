import shlex
from pathlib import Path
from typing import Any, List

from common.base_service import create_scanner_app
from common.models import ScanRequest


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def build_checkov_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    config = request.config or {}

    # Checkov prints a banner to stdout, so a plain stdout redirect would corrupt
    # the report. Instead let --output-file-path write a clean results_sarif.sarif
    # into a temp dir, then move it to the timestamped report path.
    tmp_dir = output_path.with_suffix("")  # e.g. /.../<timestamp>

    cmd = [
        "checkov",
        "-d",
        str(full_scan_path),
        "-o",
        "sarif",
        "--compact",
        "--output-file-path",
        str(tmp_dir),
    ]

    framework = _as_list(config.get("framework"))
    if framework:
        cmd.extend(["--framework", ",".join(framework)])

    for check in _as_list(config.get("check")):
        cmd.extend(["--check", check])

    for skip in _as_list(config.get("skip_check")):
        cmd.extend(["--skip-check", skip])

    inner = " ".join(shlex.quote(c) for c in cmd)
    tmp_q = shlex.quote(str(tmp_dir))
    out_q = shlex.quote(str(output_path))
    script = (
        f"mkdir -p {tmp_q} && {inner}; "
        f"mv {tmp_q}/results_sarif.sarif {out_q} 2>/dev/null; rm -rf {tmp_q}"
    )
    return ["sh", "-c", script]


app = create_scanner_app(
    tool_name="checkov",
    version_cmd=["checkov", "--version"],
    scan_cmd_builder=build_checkov_cmd,
    report_format="sarif",
    tool_category="iac",
)
