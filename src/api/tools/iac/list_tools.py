"""List available Infrastructure-as-Code (IaC) tools."""

from config.tools import tools_for_category

# Tool metadata, mirroring the shape returned by the SAST/SCA/Secrets list_tools
# tools. IaC scanners are driven by file type (Terraform, Kubernetes, Dockerfile,
# etc.) rather than a detected programming language, so there is nothing to
# filter on — every tool is always listed.
IAC_TOOLS = {
    "checkov": {
        "name": "Checkov",
        "description": (
            "Multi-framework IaC scanner (Terraform, CloudFormation, Kubernetes, "
            "Helm, ARM, Serverless, Dockerfile). Config: framework, check, skip_check"
        ),
        "languages": [],
        "category": "iac",
    },
    "kics": {
        "name": "KICS",
        "description": (
            "Checkmarx 'Keeping Infrastructure as Code Secure' — scans Terraform, "
            "Kubernetes, Docker, CloudFormation, Ansible, OpenAPI and more"
        ),
        "languages": [],
        "category": "iac",
    },
    "terrascan": {
        "name": "Terrascan",
        "description": (
            "Policy-as-code scanner for Terraform, Kubernetes, Helm and Kustomize. "
            "Config: iac_type (default terraform), policy_type"
        ),
        "languages": [],
        "category": "iac",
    },
    "tfsec": {
        "name": "TFSec",
        "description": "Static analysis security scanner for Terraform (HCL) configurations",
        "languages": [],
        "category": "iac",
    },
    "hadolint": {
        "name": "Hadolint",
        "description": "Dockerfile linter that surfaces best-practice and security issues",
        "languages": [],
        "category": "iac",
    },
}


def iac_list_tools() -> dict:
    """
    List available Infrastructure-as-Code (IaC) security scanning tools.

    Returns:
        Dictionary with available tools and their metadata
    """
    healthy = set(tools_for_category("iac"))
    available_tools = {k: v for k, v in IAC_TOOLS.items() if k in healthy}
    return {"tools": available_tools, "filtered": True}
