from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest


def build_syft_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    cmd = [
        "syft",
        "scan",
        f"dir:{str(full_scan_path)}",
        "-o",
        f"cyclonedx-json={str(output_path)}",
    ]

    config = request.config or {}

    if "scope" in config:
        cmd.extend(["--scope", config["scope"]])

    if "exclude" in config:
        for pattern in config["exclude"]:
            cmd.extend(["--exclude", pattern])

    return cmd


app = create_scanner_app(
    tool_name="syft",
    version_cmd=["syft", "version"],
    scan_cmd_builder=build_syft_cmd,
    report_format="json",  # CycloneDX JSON, not SARIF
    tool_category="sca",
)
