"""
Single source of truth for supported languages across all tools.
"""

from typing import Dict, List

# CodeQL supported languages and their extensions
CODEQL_LANGUAGES: Dict[str, List[str]] = {
    "cpp": [".cpp", ".cc", ".cxx", ".c", ".h", ".hpp"],
    "csharp": [".cs"],
    "go": [".go"],
    "java": [".java"],
    "javascript": [".js", ".jsx", ".mjs", ".cjs"],
    "kotlin": [".kt", ".kts"],
    "python": [".py"],
    "ruby": [".rb"],
    "rust": [".rs"],
    "swift": [".swift"],
    "typescript": [".ts", ".tsx"],
}

# SAST tool supported languages (kept in alphabetical order)
SEMGREP_LANGUAGES: List[str] = [
    "c",
    "cpp",
    "csharp",
    "go",
    "java",
    "javascript",
    "kotlin",
    "php",
    "python",
    "ruby",
    "rust",
    "typescript",
    "jsx",
    "scala",
    "swift",
    "php",
    "terraform",
    "generic",
    "json",
]

BANDIT_LANGUAGES: List[str] = ["python"]

GOSEC_LANGUAGES: List[str] = ["go"]

BRAKEMAN_LANGUAGES: List[str] = ["ruby"]

PMD_LANGUAGES: List[str] = [
    "apex",
    "java",
    "javascript",
    "visualforce",
    "kotlin",
    "swift",
    "modelica",
    "plsql",
    "apache_velocity",
    "jsp",
    "wsdl",
    "maven_pom",
    "html",
    "xml",
    "xsl",
]

PSALM_LANGUAGES: List[str] = ["php"]

# SCA tool supported languages
PYTHON_LANGUAGES: List[str] = ["python"]
JAVASCRIPT_LANGUAGES: List[str] = ["javascript", "typescript", "jsx", "tsx"]
