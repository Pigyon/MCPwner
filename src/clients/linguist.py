"""Linguist HTTP client for external service communication."""

from typing import Any, Dict

import requests

from clients.base import BaseClient


class LinguistClient(BaseClient):
    """HTTP client for Linguist service."""

    # Mapping from linguist to CodeQL language names
    _LANGUAGE_MAP = {
        "Python": "python",
        "JavaScript": "javascript",
        "TypeScript": "typescript",
        "Java": "java",
        "C++": "cpp",
        "C": "cpp",
        "C#": "csharp",
        "Go": "go",
        "Ruby": "ruby",
        "Swift": "swift",
        "Kotlin": "kotlin",
        "Rust": "rust",
        "Objective-C": "cpp",
        "Objective-C++": "cpp",
        "JSX": "javascript",
        "TSX": "typescript",
    }

    def __init__(self, service_url: str):
        super().__init__(service_url, "linguist")

    def detect_languages(self, workspace_path: str) -> Dict[str, Any]:
        """
        Detect languages in a workspace using linguist.

        Args:
            workspace_path: Path to the workspace directory

        Returns:
            Dictionary with language breakdown and statistics
        """
        try:
            response = requests.post(
                f"{self.service_url}/detect", json={"path": workspace_path}, timeout=60
            )
            response.raise_for_status()
            result = response.json()

            if result.get("status") != "success":
                raise RuntimeError(result.get("error", "Unknown error"))

            languages_data = result.get("languages", {})

            detected_languages = []
            language_stats = {}

            for lang_name, stats in languages_data.items():
                codeql_lang = self._map_to_codeql_language(lang_name)
                if codeql_lang:
                    detected_languages.append(codeql_lang)
                    language_stats[codeql_lang] = {
                        "original_name": lang_name,
                        "bytes": stats.get("size", 0),
                        "percentage": stats.get("percentage", 0.0),
                    }

            return {
                "languages": list(set(detected_languages)),
                "statistics": language_stats,
                "raw_output": languages_data,
            }

        except requests.exceptions.Timeout:
            raise RuntimeError("Linguist detection timed out")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Linguist service request failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Language detection failed: {e}")

    def _map_to_codeql_language(self, linguist_name: str) -> str:
        """
        Map linguist language names to CodeQL language names.

        Args:
            linguist_name: Language name from linguist

        Returns:
            CodeQL language name or None if not supported
        """
        return self._LANGUAGE_MAP.get(linguist_name)
