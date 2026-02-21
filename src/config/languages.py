"""
Configuration for supported languages across different tools.
"""

from typing import Dict, List, Set

# CodeQL supported languages and their extensions
CODEQL_LANGUAGES: Dict[str, List[str]] = {
    "python": [".py"],
    "javascript": [".js", ".jsx", ".mjs", ".cjs"],
    "typescript": [".ts", ".tsx"],
    "java": [".java"],
    "cpp": [".cpp", ".cc", ".cxx", ".c", ".h", ".hpp"],
    "csharp": [".cs"],
    "go": [".go"],
    "ruby": [".rb"],
    "swift": [".swift"],
    "kotlin": [".kt", ".kts"],
    "rust": [".rs"],
}

# Semgrep supported languages
SEMGREP_LANGUAGES: Set[str] = {
    "python",
    "javascript",
    "typescript",
    "java",
    "go",
    "ruby",
    "php",
    "c",
    "cpp",
    "csharp",
    "kotlin",
    "rust",
}

# Gosec supported languages
GOSEC_LANGUAGES: Set[str] = {"go"}

# Brakeman supported languages
BRAKEMAN_LANGUAGES: Set[str] = {"ruby"}

# Bandit supported languages
BANDIT_LANGUAGES: Set[str] = {"python"}
