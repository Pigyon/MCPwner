"""List query packs tool."""

import logging
from typing import Any, Dict, Optional

from deps import get_codeql_service

logger = logging.getLogger(__name__)


def list_query_packs(language: Optional[str] = None) -> dict:
    """
    List available CodeQL query packs by language.

    This tool queries the CodeQL CLI to discover available query packs.
    Query packs contain pre-written security queries for vulnerability detection.

    Args:
        language: Optional language filter (e.g., "python", "javascript", "java")

    Returns:
        Dictionary with available query packs grouped by language

    Example:
        list_query_packs(language="python")
    """
    try:
        codeql_service = get_codeql_service()
        result = codeql_service.list_query_packs()

        # The result from service is already structured
        return result

    except Exception as e:
        logger.error(f"Error listing query packs: {e}")
        # Fallback to defaults if service call fails
        return _get_default_packs(language)


def _get_default_packs(language: Optional[str]) -> Dict[str, Any]:
    """
    Get default query packs when CodeQL CLI is unavailable.

    Args:
        language: Optional language filter

    Returns:
        Dictionary with default packs
    """
    default_packs = [
        {
            "name": "security-extended",
            "description": "Extended security queries including medium-precision checks",
            "languages": ["all"],
        },
        {
            "name": "security-and-quality",
            "description": "Security and code quality queries",
            "languages": ["all"],
        },
    ]

    return {
        "status": "success",
        "language": language,
        "packs": default_packs,
        "note": "Showing default packs (CodeQL CLI unavailable)",
    }
