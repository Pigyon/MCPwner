"""List available tools."""


def list_tools() -> dict:
    """
    List available and planned security tools.

    Returns:
        Dictionary with available and planned tools
    """
    return {
        "available": [
            "codeql",
            "semgrep",
            "bandit",
            "gosec",
            "brakeman",
            "pmd",
            "psalm",
        ],
        "planned": ["owasp-zap"],
    }
