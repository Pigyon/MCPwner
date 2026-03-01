
import logging
import subprocess
import shutil
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
        # Always try to install/update dependencies to ensure consistency in the container
        # Use --dry-run first? No, just install.
        # If vendor exists, composer install is usually fast.
        logger.info("Ensuring dependencies are installed...")
        try:
            install_cmd = [
                "composer", "install", 
                "--no-dev", 
                "--no-scripts", 
                "--no-interaction", 
                "--ignore-platform-reqs",
                "--prefer-dist",
                "--no-progress"
            ]
            
            # If vendor exists, we might want to optimize, but let's be safe for now.
            install_result = subprocess.run(
                install_cmd,
                cwd=str(full_scan_path),
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Composer install completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Composer install failed: {e.stderr}")
            # We don't abort here, as the scan might still work partially, 
            # or the user might have provided vendor in a way we didn't expect.
            # But we log it.
    
    # Initialize basic psalm config if none exists
    # We check for psalm.xml or psalm.xml.dist
    if not (full_scan_path / "psalm.xml").exists() and not (full_scan_path / "psalm.xml.dist").exists():
         logger.info("Initializing Psalm config from fallback...")
         
         # Copy the default config from the service directory if available
         service_config = Path("/service/psalm.xml")
         if service_config.exists():
             try:
                 shutil.copy(service_config, full_scan_path / "psalm.xml")
                 logger.info("Copied default psalm.xml to workspace")
             except Exception as e:
                 logger.error(f"Failed to copy default config: {e}")
         
         # If copy failed or config missing, try init
         if not (full_scan_path / "psalm.xml").exists():
             logger.info("Running psalm --init...")
             subprocess.run(
                 ["psalm", "--init", "src", "3"],
                 cwd=str(full_scan_path),
                 capture_output=True,
                 check=False
             )

    cmd = ["psalm", "--report=" + str(output_path), "--output-format=sarif", "--root=" + str(full_scan_path)]
    
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
