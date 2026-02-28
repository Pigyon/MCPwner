
import logging
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
    
    if composer_json.exists() and not vendor_dir.exists():
        logger.info("Running composer install (existing composer.json)...")
        subprocess.run(
            ["composer", "install", "--no-dev", "--no-scripts", "--no-interaction", "--ignore-platform-reqs"],
            cwd=str(full_scan_path),
            capture_output=True,
            check=False 
        )
    elif not composer_json.exists():
        # Initialize basic psalm config if none exists
        if not (full_scan_path / "psalm.xml").exists():
             logger.info("Initializing Psalm...")
             subprocess.run(
                 ["psalm", "--init"],
                 cwd=str(full_scan_path),
                 capture_output=True,
                 check=False
             )

    cmd = ["psalm", "--report=" + str(output_path), "--output-format=sarif"]
    
    # Psalm runs from the project root usually
    # We need to execute it inside the directory
    # But our base service runs subprocess with default cwd.
    # For Psalm, it's better to pass the target directory as an argument if supported,
    # or rely on the fact that we might need to change CWD.
    # Psalm accepts file/directory arguments.
    
    cmd.append(str(full_scan_path))
    
    return cmd

app = create_scanner_app(
    tool_name="psalm",
    version_cmd=["psalm", "--version"],
    scan_cmd_builder=build_psalm_cmd
)
