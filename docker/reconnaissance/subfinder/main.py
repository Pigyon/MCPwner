"""
Subfinder Service - Subdomain Discovery Tool
"""

import logging
from pathlib import Path
from typing import List

from common.base_service import create_scanner_app
from common.models import ScanRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "subfinder"
VERSION_CMD = ["subfinder", "-version"]


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build Subfinder scan command."""
    # Get domain from config (accept both 'domain' and 'target' for compatibility)
    domain = ""
    if request.config:
        domain = request.config.get("domain") or request.config.get("target", "")

    if not domain:
        raise ValueError(
            "Domain is required in config for Subfinder scan (use 'domain' or 'target' field)"
        )

    # Subfinder command with JSON output
    cmd = ["subfinder", "-d", domain, "-json", "-o", str(output_path)]

    # Add optional parameters if provided
    if request.config:
        # Add silent mode to reduce noise
        if request.config.get("silent", True):
            cmd.append("-silent")

        # Add recursive subdomain discovery
        if request.config.get("recursive", False):
            cmd.append("-recursive")

        # Add all sources
        if request.config.get("all", False):
            cmd.append("-all")

    return cmd


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json",
    tool_category="reconnaissance",
)
