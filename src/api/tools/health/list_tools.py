"""List available tools."""


def health_list_tools() -> dict:
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
            "nodejsscan",
            "joern",
            "yasa",
            "opengrep",
        ],
        "planned": ["owasp-zap"],
    }
