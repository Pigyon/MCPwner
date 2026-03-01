from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest


def build_syft_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    # Syft command
    # scan: Generate an SBOM
    # dir: prefix to explicitly scan a directory
    # -o cyclonedx-json: Output in CycloneDX JSON format
    # --file: Output file path (deprecated but still works, or use -o format=file)
    cmd = [
        "syft",
        "scan",
        f"dir:{str(full_scan_path)}",
        "-o",
        f"cyclonedx-json={str(output_path)}",
    ]

    config = request.config or {}

    # Syft specific options
    if "scope" in config:
        # --scope <scope> (e.g. squashed, all-layers)
        cmd.extend(["--scope", config["scope"]])

    # Exclude patterns
    if "exclude" in config:
        for pattern in config["exclude"]:
            cmd.extend(["--exclude", pattern])

    return cmd


app = create_scanner_app(
    tool_name="syft",
    version_cmd=["syft", "version"],
    scan_cmd_builder=build_syft_cmd,
    report_format="json",  # Syft outputs JSON for CycloneDX, not SARIF
    tool_category="sca",
)
