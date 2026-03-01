from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest


def build_brakeman_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    cmd = ["brakeman", "-f", "sarif", "-o", str(output_path)]

    config = request.config or {}

    if "confidence" in config and config["confidence"]:
        confidence_levels = config["confidence"]
        if isinstance(confidence_levels, list):
            # Map confidence levels to Brakeman's -w flag (warning levels)
            # Brakeman uses confidence levels: 0 (high), 1 (medium), 2 (weak/low)
            min_confidence = min(
                [{"high": 0, "medium": 1, "low": 2}.get(c.lower(), 2) for c in confidence_levels]
            )
            cmd.extend(["-w", str(min_confidence)])

    cmd.extend(["-p", str(full_scan_path)])
    return cmd


app = create_scanner_app(
    tool_name="brakeman", version_cmd=["brakeman", "--version"], scan_cmd_builder=build_brakeman_cmd
)
