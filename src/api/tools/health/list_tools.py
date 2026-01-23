"""List available tools."""


def list_tools() -> dict:
    """
    List available and planned security tools.
    
    Returns:
        Dictionary with available and planned tools
    """
    return {
        "available": ["codeql"],
        "planned": ["semgrep", "owasp-zap"]
    }
