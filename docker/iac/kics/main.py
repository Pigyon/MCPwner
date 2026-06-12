from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest

# Bundled query/library assets copied from the vendor image. KICS resolves these
# relative to its CWD by default, so they must be passed explicitly.
QUERIES_PATH = "/app/bin/assets/queries"
LIBRARIES_PATH = "/app/bin/assets/libraries"


def build_kics_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    # KICS writes "<output-name>.<format>" inside the -o directory. Point those at
    # the timestamped report path the platform expects (<dir>/<stem>.sarif).
    cmd = [
        "kics",
        "scan",
        "-p",
        str(full_scan_path),
        "--report-formats",
        "sarif",
        "-o",
        str(output_path.parent),
        "--output-name",
        output_path.stem,
        "-q",
        QUERIES_PATH,
        "--libraries-path",
        LIBRARIES_PATH,
        "--no-progress",
    ]

    config = request.config or {}

    # Restrict to specific platforms (terraform, k8s, dockerfile, cloudformation, ...)
    if config.get("type"):
        types = config["type"]
        cmd.extend(["-t", ",".join(types) if isinstance(types, list) else types])

    # Comma-separated paths to exclude from the scan
    if config.get("exclude_paths"):
        cmd.extend(["--exclude-paths", ",".join(config["exclude_paths"])])

    return cmd


app = create_scanner_app(
    tool_name="kics",
    version_cmd=["kics", "version"],
    scan_cmd_builder=build_kics_cmd,
    report_format="sarif",
    tool_category="iac",
)
