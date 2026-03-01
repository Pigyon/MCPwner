
from pathlib import Path
from common.base_service import create_scanner_app
from common.models import ScanRequest

def build_osv_scanner_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path
    
    # OSV-Scanner V2 command
    # The "Starting filesystem walk for root: /" suggests OSV-Scanner is misinterpreting the path
    # Let's try using -r with the path immediately after it (old V1 style)
    # Or use the directory without --recursive flag
    
    # Make sure the path is absolute
    abs_scan_path = full_scan_path.resolve()
    
    # Try without --recursive flag, just scan the directory
    cmd = [
        "osv-scanner",
        "scan",
        "-r",
        str(abs_scan_path),
        "--format",
        "sarif",
        "--output",
        str(output_path),
    ]
    
    config = request.config or {}
    
    # Config file
    if "config" in config:
        # --config <path>
        cmd.extend(["--config", config["config"]])
    
    # Call-analysis for better results
    if config.get("call_analysis", False):
        cmd.append("--call-analysis")
        
    return cmd

app = create_scanner_app(
    tool_name="osv-scanner",
    version_cmd=["osv-scanner", "version"],
    scan_cmd_builder=build_osv_scanner_cmd,
    report_format="sarif",
    tool_category="sca"
)
