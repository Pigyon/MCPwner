"""Linguist service for language detection."""

from pathlib import Path
from typing import Any, Dict, List

from clients.linguist import LinguistClient
from config.languages import CODEQL_LANGUAGES
from repositories.workspace import WorkspaceRepository


class LinguistService:
    """Service for language detection operations."""

    def __init__(self, repository: WorkspaceRepository, linguist_client: LinguistClient = None):
        self.repository = repository
        self.linguist_client = linguist_client or LinguistClient()

    def detect_languages(self, workspace_id: str, filter_codeql: bool = True) -> List[str]:
        """
        Detect programming languages in a workspace using linguist.

        Args:
            workspace_id: UUID of the workspace
            filter_codeql: If True, only return CodeQL-supported languages

        Returns:
            List of detected language names (e.g., ["python", "javascript"])
        """
        workspace = self.repository.find_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")

        workspace_path = workspace.path or workspace.local_path
        if not workspace_path:
            raise ValueError(f"No source path for workspace: {workspace_id}")

        workspace_dir = Path(workspace_path)
        if not workspace_dir.exists():
            return []

        try:
            # Use linguist for language detection
            result = self.linguist_client.detect_languages(str(workspace_dir))
            detected_languages = result.get("languages", [])

            # Filter to only CodeQL-supported languages if requested
            if filter_codeql:
                detected_languages = [
                    lang for lang in detected_languages if lang in CODEQL_LANGUAGES
                ]

            return sorted(detected_languages)

        except Exception as e:
            raise RuntimeError(f"Language detection failed: {e}")

    def detect_languages_detailed(self, workspace_id: str) -> Dict[str, Any]:
        """
        Detect languages with detailed statistics.

        Args:
            workspace_id: UUID of the workspace

        Returns:
            Dictionary with languages, statistics, and raw output
        """
        workspace = self.repository.find_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")

        workspace_path = workspace.path or workspace.local_path
        if not workspace_path:
            raise ValueError(f"No source path for workspace: {workspace_id}")

        workspace_dir = Path(workspace_path)
        if not workspace_dir.exists():
            return {"languages": [], "statistics": {}, "raw_output": {}}

        try:
            return self.linguist_client.detect_languages(str(workspace_dir))
        except Exception as e:
            raise RuntimeError(f"Language detection failed: {e}")
