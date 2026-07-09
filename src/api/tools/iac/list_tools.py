"""List available Infrastructure-as-Code (IaC) tools."""

from typing import Optional

from api.tools.common import filter_tools_by_language, handle_tool_error

IAC_TOOLS = {
    "checkov": {
        "name": "Checkov",
        "description": (
            "Multi-framework IaC scanner (Terraform, CloudFormation, Kubernetes, "
            "Helm, ARM, Serverless, Dockerfile). Config: framework, check, skip_check"
        ),
        "languages": [],
    },
    "kics": {
        "name": "KICS",
        "description": (
            "Checkmarx 'Keeping Infrastructure as Code Secure' — scans Terraform, "
            "Kubernetes, Docker, CloudFormation, Ansible, OpenAPI and more"
        ),
        "languages": [],
    },
    "terrascan": {
        "name": "Terrascan",
        "description": (
            "Policy-as-code scanner for Terraform, Kubernetes, Helm and Kustomize. "
            "Config: iac_type (default terraform), policy_type"
        ),
        "languages": [],
    },
    "tfsec": {
        "name": "TFSec",
        "description": "Static analysis security scanner for Terraform (HCL) configurations",
        "languages": [],
    },
    "hadolint": {
        "name": "Hadolint",
        "description": "Dockerfile linter that surfaces best-practice and security issues",
        "languages": [],
    },
}


@handle_tool_error
def iac_list_tools(workspace_id: Optional[str] = None, show_all: bool = False) -> dict:
    """
    List available Infrastructure-as-Code (IaC) security scanning tools.

    Returns:
        Dictionary with available tools and their metadata
    """
    return filter_tools_by_language("iac", IAC_TOOLS, workspace_id, show_all)
