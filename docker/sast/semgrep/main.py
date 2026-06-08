import os
from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest

# Default ruleset. 'auto' pulls the curated Semgrep Registry ruleset (needs
# internet); a bundled path can be set via SEMGREP_DEFAULT_CONFIG for offline use.
DEFAULT_CONFIG = os.environ.get("SEMGREP_DEFAULT_CONFIG", "auto")


def build_semgrep_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    config = request.config or {}
    configs = config["rules"] if config.get("rules") else [DEFAULT_CONFIG]

    cmd = ["semgrep", "scan", "--sarif", "--output", str(output_path)]

    # 'auto' fetches from the registry and *requires* metrics to be enabled;
    # for any explicit/bundled config, disable metrics so semgrep stays quiet.
    if "auto" not in configs:
        cmd.extend(["--metrics", "off"])

    for rule in configs:
        cmd.extend(["--config", rule])

    if "exclude" in config:
        for pattern in config["exclude"]:
            cmd.extend(["--exclude", pattern])

    cmd.append(str(full_scan_path))
    return cmd


app = create_scanner_app(
    tool_name="semgrep", version_cmd=["semgrep", "--version"], scan_cmd_builder=build_semgrep_cmd
)
