from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest


def build_osv_scanner_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path
    abs_scan_path = full_scan_path.resolve()

    cmd = [
        "osv-scanner",
        "scan",
        "-r",
        str(abs_scan_path),
        "--format",
        "sarif",
        "--output",
        str(output_path),
    ]

    config = request.config or {}

    if "config" in config:
        cmd.extend(["--config", config["config"]])

    if config.get("call_analysis", False):
        cmd.append("--call-analysis")

    return cmd


app = create_scanner_app(
    tool_name="osv-scanner",
    version_cmd=["osv-scanner", "version"],
    scan_cmd_builder=build_osv_scanner_cmd,
    report_format="sarif",
    tool_category="sca",
)
