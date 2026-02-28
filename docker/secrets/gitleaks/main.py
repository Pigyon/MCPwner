"""
Gitleaks Service - Secrets Detection
"""

import logging
from pathlib import Path
from typing import List

from common.base_service import create_scanner_app
from common.models import ScanRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "gitleaks"
VERSION_CMD = ["gitleaks", "version"]


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build Gitleaks scan command."""
    # Build command
    cmd = [
        "gitleaks",
        "detect",
        "--source",
        str(request.workspace_path),
        "--report-path",
        str(output_path),
        "--report-format",
        "sarif",
        "--no-git",  # Scan files directly
        "--exit-code",
        "0",  # Force exit code 0 even if leaks found (or rely on base_service handling)
        # Actually, base_service handles non-zero exit codes, so we don't strictly need this,
        # but it's safer to ensure consistent behavior if we wanted check=True.
        # However, base_service uses check=False.
        # Let's keep it simple.
        "--verbose",
    ]

    # If scan_path is provided, update source
    if request.scan_path:
        full_source = Path(request.workspace_path) / request.scan_path
        cmd[3] = str(full_source)

    return cmd


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="sarif",
    tool_category="secrets",
)
