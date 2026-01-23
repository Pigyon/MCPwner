"""List query packs tool."""

from fastmcp import tool


@tool()
def list_query_packs(language: str = None) -> list:
    """
    List available CodeQL query packs by language.
    
    Args:
        language: Optional language filter
        
    Returns:
        Array of query pack names
    """
    return ["security-extended", "security-and-quality"]
