import logging
import shutil
import subprocess
from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest

logger = logging.getLogger(__name__)


def build_psalm_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    # Psalm needs composer autoloading to resolve classes.
    # Install dependencies if composer.json exists but vendor/ doesn't.
    composer_json = full_scan_path / "composer.json"
    vendor_dir = full_scan_path / "vendor"

    if composer_json.exists():
        logger.info("Ensuring dependencies are installed...")
        try:
            install_cmd = [
                "composer",
                "install",
                "--no-dev",
                "--no-scripts",
                "--no-interaction",
                "--ignore-platform-reqs",
                "--prefer-dist",
                "--no-progress",
            ]

            install_result = subprocess.run(
                install_cmd, cwd=str(full_scan_path), capture_output=True, text=True, check=True
            )
            logger.info("Composer install completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Composer install failed: {e.stderr}")
            # Non-fatal: scan may still work with a partial vendor tree.

    if not (full_scan_path / "psalm.xml").exists() and not (full_scan_path / "psalm.xml.dist").exists():
        logger.info("Initializing Psalm config from fallback...")

        service_config = Path("/service/psalm.xml")
        if service_config.exists():
            try:
                shutil.copy(service_config, full_scan_path / "psalm.xml")
                logger.info("Copied default psalm.xml to workspace")
            except Exception as e:
                logger.error(f"Failed to copy default config: {e}")

        if not (full_scan_path / "psalm.xml").exists():
            logger.info("Running psalm --init...")
            subprocess.run(
                ["psalm", "--init", "src", "3"],
                cwd=str(full_scan_path),
                capture_output=True,
                check=False,
            )

    cmd = [
        "psalm",
        "--report=" + str(output_path),
        "--output-format=sarif",
        "--root=" + str(full_scan_path),
        # Disable the on-disk cache: psalm runs non-root on a read-only rootfs and
        # otherwise crashes trying to create its cache directory.
        "--no-cache",
    ]

    cmd.append(str(full_scan_path))

    return cmd


app = create_scanner_app(
    tool_name="psalm", version_cmd=["psalm", "--version"], scan_cmd_builder=build_psalm_cmd
)
