from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest


def build_nodejsscan_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    # nodejsscan CLI: nodejsscan -d <dir> -o <output.json>
    cmd = ["nodejsscan", "-d", str(full_scan_path), "-o", str(output_path)]

    return cmd


app = create_scanner_app(
    tool_name="nodejsscan",
    version_cmd=["nodejsscan", "--version"],
    scan_cmd_builder=build_nodejsscan_cmd,
    report_format="json",
)
