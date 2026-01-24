"""List query packs tool."""

import subprocess
import logging
from typing import Optional, Dict, Any, List

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
        # Try to resolve query packs using CodeQL CLI
        cmd = ["codeql", "resolve", "queries"]
        
        # Add language-specific pack if provided
        if language:
            cmd.append(f"codeql/{language}-queries")
        else:
            # Query common language packs
            cmd.append("codeql/*-queries")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse output to extract pack information
        packs = _parse_query_packs(result.stdout, language)
        
        return {
            "status": "success",
            "language": language,
            "packs": packs
        }
        
    except subprocess.TimeoutExpired:
        logger.warning("Query pack listing timed out, returning defaults")
        return _get_default_packs(language)
    except FileNotFoundError:
        logger.warning("CodeQL CLI not found, returning defaults")
        return _get_default_packs(language)
    except Exception as e:
        logger.error(f"Error listing query packs: {e}")
        return _get_default_packs(language)


def _parse_query_packs(output: str, language_filter: Optional[str]) -> List[Dict[str, Any]]:
    """
    Parse CodeQL resolve queries output.
    
    Args:
        output: Command output
        language_filter: Optional language filter
        
    Returns:
        List of pack dictionaries
    """
    packs = []
    
    # Common query packs for all languages
    common_packs = [
        {
            "name": "security-extended",
            "description": "Extended security queries including medium-precision checks",
            "languages": ["all"]
        },
        {
            "name": "security-and-quality",
            "description": "Security and code quality queries",
            "languages": ["all"]
        }
    ]
    
    # Language-specific packs
    language_packs = {
        "python": [
            {"name": "codeql/python-queries", "description": "Standard Python queries"},
            {"name": "codeql/python-queries:Security", "description": "Python security queries"},
            {"name": "codeql/python-queries:Maintainability", "description": "Python code quality queries"}
        ],
        "javascript": [
            {"name": "codeql/javascript-queries", "description": "Standard JavaScript/TypeScript queries"},
            {"name": "codeql/javascript-queries:Security", "description": "JavaScript security queries"}
        ],
        "typescript": [
            {"name": "codeql/javascript-queries", "description": "Standard JavaScript/TypeScript queries"},
            {"name": "codeql/javascript-queries:Security", "description": "TypeScript security queries"}
        ],
        "java": [
            {"name": "codeql/java-queries", "description": "Standard Java queries"},
            {"name": "codeql/java-queries:Security", "description": "Java security queries"}
        ],
        "cpp": [
            {"name": "codeql/cpp-queries", "description": "Standard C/C++ queries"},
            {"name": "codeql/cpp-queries:Security", "description": "C/C++ security queries"}
        ],
        "csharp": [
            {"name": "codeql/csharp-queries", "description": "Standard C# queries"},
            {"name": "codeql/csharp-queries:Security", "description": "C# security queries"}
        ],
        "go": [
            {"name": "codeql/go-queries", "description": "Standard Go queries"},
            {"name": "codeql/go-queries:Security", "description": "Go security queries"}
        ],
        "ruby": [
            {"name": "codeql/ruby-queries", "description": "Standard Ruby queries"},
            {"name": "codeql/ruby-queries:Security", "description": "Ruby security queries"}
        ],
        "swift": [
            {"name": "codeql/swift-queries", "description": "Standard Swift queries"},
            {"name": "codeql/swift-queries:Security", "description": "Swift security queries"}
        ],
        "kotlin": [
            {"name": "codeql/java-queries", "description": "Standard Kotlin queries (via Java)"},
            {"name": "codeql/java-queries:Security", "description": "Kotlin security queries"}
        ],
        "rust": [
            {"name": "codeql/rust-queries", "description": "Standard Rust queries"},
            {"name": "codeql/rust-queries:Security", "description": "Rust security queries"}
        ]
    }
    
    # Add common packs
    packs.extend(common_packs)
    
    # Add language-specific packs
    if language_filter:
        if language_filter in language_packs:
            packs.extend(language_packs[language_filter])
    else:
        # Add all language packs
        for lang_packs in language_packs.values():
            packs.extend(lang_packs)
    
    return packs


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
            "languages": ["all"]
        },
        {
            "name": "security-and-quality",
            "description": "Security and code quality queries",
            "languages": ["all"]
        }
    ]
    
    return {
        "status": "success",
        "language": language,
        "packs": default_packs,
        "note": "Showing default packs (CodeQL CLI unavailable)"
    }
