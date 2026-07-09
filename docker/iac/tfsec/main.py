from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest


def build_tfsec_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    # tfsec writes SARIF straight to --out, so the factory's output_path is used as-is.
    cmd = [
        "tfsec",
        str(full_scan_path),
        "--format",
        "sarif",
        "--out",
        str(output_path),
        "--no-color",
    ]

    config = request.config or {}

    if config.get("minimum_severity"):
        cmd.extend(["--minimum-severity", config["minimum_severity"]])

    if config.get("exclude"):
        cmd.extend(["--exclude", ",".join(config["exclude"])])

    return cmd


app = create_scanner_app(
    tool_name="tfsec",
    version_cmd=["tfsec", "--version"],
    scan_cmd_builder=build_tfsec_cmd,
    report_format="sarif",
    tool_category="iac",
)
