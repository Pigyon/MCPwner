from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest


def build_retirejs_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    cmd = [
        "retire",
        "--outputformat",
        "json",
        "--outputpath",
        str(output_path),
        str(full_scan_path),
    ]

    config = request.config or {}

    if "ignore" in config:
        for ignore_item in config["ignore"]:
            cmd.extend(["--ignore", ignore_item])

    if "severity" in config:
        cmd.extend(["--severity", config["severity"]])

    return cmd


app = create_scanner_app(
    tool_name="retirejs",
    version_cmd=["retire", "--version"],
    scan_cmd_builder=build_retirejs_cmd,
    report_format="json",
    tool_category="sca",
)
