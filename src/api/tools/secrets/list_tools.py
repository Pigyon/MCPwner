"""List available Secrets tools."""

from typing import List

SECRETS_TOOLS = ["gitleaks", "trufflehog", "whispers"]


def secrets_list_tools() -> List[str]:
    """
    List available Secrets scanning tools.

    Returns:
        List of tool names
    """
    return SECRETS_TOOLS
