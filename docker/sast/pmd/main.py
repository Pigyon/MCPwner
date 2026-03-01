
from pathlib import Path
from common.base_service import create_scanner_app
from common.models import ScanRequest

def build_pmd_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path
    
    # PMD 7.x uses: pmd check --dir <path> --rulesets <rulesets> --format sarif --report-file <output>
    cmd = [
        "pmd",
        "check",
        "--dir",
        str(full_scan_path),
        "--format",
        "sarif",
        "--report-file",
        str(output_path),
    ]
    
    config = request.config or {}
    
    # Add rulesets
    if "rulesets" in config and config["rulesets"]:
        cmd.extend(["--rulesets", ",".join(config["rulesets"])])
    else:
        # Default rulesets if none provided
        cmd.extend(["--rulesets", "rulesets/java/quickstart.xml"])
        
    return cmd

app = create_scanner_app(
    tool_name="pmd",
    version_cmd=["pmd", "--version"],
    scan_cmd_builder=build_pmd_cmd
)
