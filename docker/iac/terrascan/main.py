import shlex
from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest


def build_terrascan_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    config = request.config or {}
    # Terrascan scans one IaC type per run; terraform is the most common default.
    iac_type = config.get("iac_type", "terraform")

    cmd = ["terrascan", "scan", "-i", iac_type, "-d", str(full_scan_path), "-o", "sarif"]

    # Restrict to specific policy/cloud providers (aws, gcp, azure, k8s, github, ...)
    if config.get("policy_type"):
        policy_type = config["policy_type"]
        for provider in policy_type if isinstance(policy_type, list) else [policy_type]:
            cmd.extend(["-t", provider])

    # Terrascan emits the SARIF report on stdout (diagnostics go to stderr), so
    # redirect stdout into the report file the platform expects.
    script = " ".join(shlex.quote(c) for c in cmd) + f" > {shlex.quote(str(output_path))}"
    return ["sh", "-c", script]


app = create_scanner_app(
    tool_name="terrascan",
    version_cmd=["terrascan", "version"],
    scan_cmd_builder=build_terrascan_cmd,
    report_format="sarif",
    tool_category="iac",
)
