import logging
from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest

logger = logging.getLogger(__name__)


def build_opengrep_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    cmd = ["opengrep", "scan", "--sarif", "--output", str(output_path)]

    config = request.config or {}

    if "rules" in config:
        for rule in config["rules"]:
            cmd.extend(["--config", rule])
    else:
        cmd.extend(["--config", "auto"])

    if "exclude" in config:
        for pattern in config["exclude"]:
            cmd.extend(["--exclude", pattern])

    if "severity" in config:
        cmd.extend(["--severity", config["severity"].upper()])

    cmd.append(str(full_scan_path))
    return cmd


app = create_scanner_app(
    tool_name="opengrep",
    version_cmd=["opengrep", "--version"],
    scan_cmd_builder=build_opengrep_cmd,
    report_format="sarif",
)
