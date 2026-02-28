
from pathlib import Path
from common.base_service import create_scanner_app
from common.models import ScanRequest

def build_bandit_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path
    
    cmd = ["bandit", "-f", "json", "-o", str(output_path)]
    
    config = request.config or {}
    
    # Severity filtering
    if "severity" in config:
        severity = config["severity"].lower()
        if severity == "high":
            cmd.append("-lll")
        elif severity == "medium":
            cmd.append("-ll")
            
    # Confidence filtering
    if "confidence" in config:
        confidence = config["confidence"].lower()
        if confidence == "high":
            cmd.append("-iii")
        elif confidence == "medium":
            cmd.append("-ii")
            
    # Recursive scan
    cmd.append("-r")
    cmd.append(str(full_scan_path))
    
    # Exclude paths
    if "exclude" in config:
        cmd.extend(["-x", ",".join(config["exclude"])])
        
    return cmd

app = create_scanner_app(
    tool_name="bandit",
    version_cmd=["bandit", "--version"],
    scan_cmd_builder=build_bandit_cmd,
    report_format="json" # Bandit outputs JSON by default in this config
)
