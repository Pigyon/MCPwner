import os
from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest

# Ruleset bundled into the image at build time (see Dockerfile). Used as the
# default so scans run offline; 'auto' would require network access to the
# semgrep registry, which the internal SAST network forbids.
DEFAULT_CONFIG = os.environ.get("SEMGREP_DEFAULT_CONFIG", "auto")


def build_semgrep_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    # --metrics off prevents semgrep from phoning home (would fail/stall offline).
    cmd = ["semgrep", "scan", "--metrics", "off", "--sarif", "--output", str(output_path)]

    config = request.config or {}
    if "rules" in config:
        for rule in config["rules"]:
            cmd.extend(["--config", rule])
    else:
        cmd.extend(["--config", DEFAULT_CONFIG])

    if "exclude" in config:
        for pattern in config["exclude"]:
            cmd.extend(["--exclude", pattern])

    cmd.append(str(full_scan_path))
    return cmd


app = create_scanner_app(
    tool_name="semgrep", version_cmd=["semgrep", "--version"], scan_cmd_builder=build_semgrep_cmd
)
