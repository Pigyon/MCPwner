"""
Hawk-Scanner Service - Secrets Detection
"""

import json
import logging
from pathlib import Path
from typing import List

from common.base_service import create_scanner_app
from common.models import ScanRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "hawk-scanner"
VERSION_CMD = ["pip", "show", "hawk-scanner"]


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build Hawk-Scanner scan command."""
    # hawk_scanner fs --connection-json ... --json output.json

    # We need to construct connection json for fs scan
    scan_path = Path(request.workspace_path)
    if request.scan_path:
        scan_path = scan_path / request.scan_path

    connection_config = {"sources": {"fs": {"scan1": {"path": str(scan_path)}}}}

    connection_json = json.dumps(connection_config)

    cmd = [
        "hawk_scanner",
        "fs",
        "--connection-json",
        connection_json,
        "--json",
        str(output_path),
        "--stdout",
    ]

    return cmd


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json",
    tool_category="secrets",
)
