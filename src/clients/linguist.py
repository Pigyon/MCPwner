"""Linguist HTTP client for external service communication."""

import requests
from typing import Dict, Any


class LinguistClient:
    """HTTP client for Linguist service."""
    
    def __init__(self, service_url: str):
        self.service_url = service_url.rstrip('/')
    
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
                f"{self.service_url}/detect",
                json={"path": workspace_path},
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") != "success":
                raise RuntimeError(result.get("error", "Unknown error"))
            
            languages_data = result.get("languages", {})
            
            # Extract language names and map to CodeQL-compatible names
            detected_languages = []
            language_stats = {}
            
            for lang_name, stats in languages_data.items():
                # Map linguist names to CodeQL language names
                codeql_lang = self._map_to_codeql_language(lang_name)
                if codeql_lang:
                    detected_languages.append(codeql_lang)
                    language_stats[codeql_lang] = {
                        "original_name": lang_name,
                        "bytes": stats.get("size", 0),
                        "percentage": stats.get("percentage", 0.0)
                    }
            
            return {
                "languages": list(set(detected_languages)),  # Remove duplicates
                "statistics": language_stats,
                "raw_output": languages_data
            }
            
        except requests.exceptions.Timeout:
            raise RuntimeError("Linguist detection timed out")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Linguist service request failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Language detection failed: {e}")
    
    def get_version(self) -> Dict[str, Any]:
        """Get linguist version via HTTP."""
        response = requests.get(
            f"{self.service_url}/version",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    def _map_to_codeql_language(self, linguist_name: str) -> str:
        """
        Map linguist language names to CodeQL language names.
        
        Args:
            linguist_name: Language name from linguist
            
        Returns:
            CodeQL language name or None if not supported
        """
        # Mapping from linguist to CodeQL language names
        language_map = {
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
            "TSX": "typescript"
        }
        
        return language_map.get(linguist_name)
