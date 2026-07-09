from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest


def build_grype_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    cmd = [
        "grype",
        f"dir:{str(full_scan_path)}",
        "-o",
        "sarif",
        "--file",
        str(output_path),
    ]

    config = request.config or {}

    if "fail_on" in config:
        cmd.extend(["--fail-on", config["fail_on"]])

    if config.get("only_fixed", False):
        cmd.append("--only-fixed")

    if "scope" in config:
        cmd.extend(["--scope", config["scope"]])

    if "exclude" in config:
        for pattern in config["exclude"]:
            cmd.extend(["--exclude", pattern])

    return cmd


app = create_scanner_app(
    tool_name="grype",
    version_cmd=["grype", "version"],
    scan_cmd_builder=build_grype_cmd,
    report_format="sarif",
    tool_category="sca",
)
