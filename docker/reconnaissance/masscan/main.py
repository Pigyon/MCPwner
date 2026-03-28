"""
Masscan Service - Fast Port Scanner
"""

import logging
import socket
from pathlib import Path
from typing import List

from common.base_service import create_scanner_app
from common.models import ScanRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "masscan"
VERSION_CMD = ["masscan", "--version"]


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build Masscan scan command."""
    # Get target from config
    target = ""
    if request.config:
        target = request.config.get("target", "")

    if not target:
        raise ValueError("Target is required in config for Masscan scan (use 'target' field)")

    # Resolve hostname to IP if needed (masscan doesn't resolve hostnames)
    try:
        # Check if target is already an IP address
        socket.inet_aton(target)
        resolved_target = target
    except socket.error:
        # Not an IP, try to resolve hostname
        try:
            resolved_target = socket.gethostbyname(target)
            logger.info(f"Resolved {target} to {resolved_target}")
        except socket.gaierror as e:
            raise ValueError(f"Failed to resolve hostname {target}: {e}")

    # Get ports (default to common ports)
    ports = "1-1000"
    if request.config:
        ports = request.config.get("ports", ports)

    # Masscan command with JSON output (-oJ)
    # Correct syntax: masscan -p<ports> --rate <rate> <target> -oJ <output>
    cmd = ["masscan", "-p", ports]

    # Add optional parameters before target
    if request.config:
        # Rate limit (packets per second, default to 100 for safety)
        rate = request.config.get("rate", 100)
        cmd.extend(["--rate", str(rate)])

        # Add exclude targets
        exclude = request.config.get("exclude")
        if exclude:
            cmd.extend(["--exclude", exclude])

        # Add banners (grab service banners)
        if request.config.get("banners", False):
            cmd.append("--banners")
    else:
        cmd.extend(["--rate", "100"])

    # Add resolved target and output file
    cmd.append(resolved_target)
    cmd.extend(["-oJ", str(output_path)])

    # Masscan requires --wait to flush results before exit (default 10s is fine)
    cmd.extend(["--wait", "5"])

    logger.info(f"Built masscan command: {cmd}")
    return cmd


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json",
    tool_category="reconnaissance",
)
