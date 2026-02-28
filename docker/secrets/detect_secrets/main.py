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
    # detect-secrets prints to stdout, so we use shell redirection
    cmd_str = f"detect-secrets scan {request.workspace_path} > {output_path}"
    
    if request.scan_path:
        full_source = Path(request.workspace_path) / request.scan_path
        cmd_str = f"detect-secrets scan {full_source} > {output_path}"

    return ["sh", "-c", cmd_str]


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json",
    tool_category="secrets",
)
