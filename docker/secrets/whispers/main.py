"""
Whispers Service - Secrets Detection
"""

import logging
from pathlib import Path
from typing import List

from common.base_service import create_scanner_app
from common.models import ScanRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "whispers"
VERSION_CMD = ["whispers", "--version"]


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build Whispers scan command."""
    # Build command
    cmd = [
        "whispers",
        str(request.workspace_path),
        "--output",
        str(output_path),
    ]

    # If scan_path is provided, update source
    if request.scan_path:
        full_source = Path(request.workspace_path) / request.scan_path
        cmd[1] = str(full_source)

    return cmd


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json",
    tool_category="secrets",
)
