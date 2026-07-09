from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest


def build_gosec_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    cmd = ["gosec", "-fmt=sarif", "-out", str(output_path)]

    config = request.config or {}

    if "severity" in config:
        severity = config["severity"]
        if severity:
            cmd.extend(["-severity", severity])

    if "confidence" in config:
        confidence = config["confidence"]
        if confidence:
            cmd.extend(["-confidence", confidence])

    if "exclude" in config:
        for pattern in config["exclude"]:
            cmd.extend(["-exclude", pattern])

    cmd.append(str(full_scan_path) + "/...")

    return cmd


app = create_scanner_app(
    tool_name="gosec", version_cmd=["gosec", "-version"], scan_cmd_builder=build_gosec_cmd
)
