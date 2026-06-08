"""
Detect-Secrets Service - Secrets Detection
"""

import logging
from pathlib import Path
from typing import List

from common.base_service import create_scanner_app
from common.models import ScanRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "detect-secrets"
VERSION_CMD = ["detect-secrets", "--version"]


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build Detect-Secrets scan command."""
    source = request.workspace_path
    if request.scan_path:
        source = str(Path(request.workspace_path) / request.scan_path)

    # detect-secrets prints to stdout, so we need shell redirection. Pass the
    # source and output paths as positional args ($1, $2) instead of
    # interpolating them into the command string, so they can never be parsed
    # as shell metacharacters (command-injection safe).
    cmd_str = 'detect-secrets scan --all-files "$1" > "$2"'
    return ["sh", "-c", cmd_str, "sh", source, str(output_path)]


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json",
    tool_category="secrets",
)
