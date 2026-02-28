"""
TruffleHog Service - Secrets Detection
"""

import logging
import shlex
from pathlib import Path
from typing import List

from common.base_service import create_scanner_app
from common.models import ScanRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "trufflehog"
VERSION_CMD = ["trufflehog", "--version"]


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build TruffleHog scan command."""
    # TruffleHog filesystem scan command
    # trufflehog filesystem [path] --json
    
    cmd = [
        "trufflehog",
        "filesystem",
        str(request.workspace_path),
        "--json",
        "--fail", # Fail with exit code 1 if secrets are found
        "--no-verification", # Faster, doesn't verify secrets against API
    ]
    
    if request.scan_path:
        full_source = Path(request.workspace_path) / request.scan_path
        cmd[2] = str(full_source)
        
    # Wrap in sh -c to redirect output to file
    safe_cmd = " ".join(shlex.quote(arg) for arg in cmd)
    
    wrapped_cmd = [
        "sh",
        "-c",
        f"{safe_cmd} > {shlex.quote(str(output_path))}"
    ]
    
    return wrapped_cmd


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json", # TruffleHog outputs JSON (NDJSON actually, but handled by base_service)
    tool_category="secrets",
)
