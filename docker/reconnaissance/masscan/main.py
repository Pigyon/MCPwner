"""
Masscan Service - Fast Port Scanner
"""

import logging
import socket
import time
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
    target = ""
    if request.config:
        target = request.config.get("target", "")

    if not target:
        raise ValueError("Target is required in config for Masscan scan (use 'target' field)")

    # Resolve hostname to IP if needed (masscan doesn't resolve hostnames)
    try:
        socket.inet_aton(target)
        resolved_target = target
    except socket.error:
        # Docker DNS (127.0.0.11) can transiently fail under load; retry with backoff.
        resolved_target = None
        last_error = None
        for attempt in range(3):
            try:
                resolved_target = socket.gethostbyname(target)
                logger.info(f"Resolved {target} to {resolved_target}")
                break
            except socket.gaierror as e:
                last_error = e
                logger.warning(f"DNS resolution for {target} failed (attempt {attempt + 1}/3): {e}")
                time.sleep(1)
        if resolved_target is None:
            raise ValueError(f"Failed to resolve hostname {target}: {last_error}")

    ports = "1-1000"
    if request.config:
        ports = request.config.get("ports", ports)

    cmd = ["masscan", "-p", ports]

    if request.config:
        rate = request.config.get("rate", 100)
        cmd.extend(["--rate", str(rate)])

        exclude = request.config.get("exclude")
        if exclude:
            cmd.extend(["--exclude", exclude])

        if request.config.get("banners", False):
            cmd.append("--banners")
    else:
        cmd.extend(["--rate", "100"])

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
