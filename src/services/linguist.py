"""Linguist service for language detection and code-facts indexing."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from clients.linguist import LinguistClient
from config.languages import CODEQL_LANGUAGES
from repositories.workspace import WorkspaceRepository

logger = logging.getLogger(__name__)


class LinguistService:
    """Service for language detection operations."""

    def __init__(self, repository: WorkspaceRepository, linguist_client: LinguistClient):
        self.repository = repository
        self.linguist_client = linguist_client

    def detect_languages(self, workspace_id: str, filter_codeql: bool = True) -> List[str]:
        """
        Detect programming languages in a workspace using linguist.

        Args:
            workspace_id: UUID of the workspace
            filter_codeql: If True, only return CodeQL-supported languages

        Returns:
            List of detected language names (e.g., ["python", "javascript"])
        """
        workspace_path = self.repository.get_valid_workspace_path(workspace_id)

        workspace_dir = Path(workspace_path)
        if not workspace_dir.exists():
            return []

        try:
            result = self.linguist_client.detect_languages(str(workspace_dir))
            detected_languages = result.get("languages", [])

            if filter_codeql:
                detected_languages = [lang for lang in detected_languages if lang in CODEQL_LANGUAGES]

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
        workspace_path = self.repository.get_valid_workspace_path(workspace_id)

        workspace_dir = Path(workspace_path)
        if not workspace_dir.exists():
            return {"languages": [], "statistics": {}, "raw_output": {}}

        try:
            return self.linguist_client.detect_languages(str(workspace_dir))
        except Exception as e:
            raise RuntimeError(f"Language detection failed: {e}")

    def _facts_path(self, workspace_id: str) -> Path:
        """Index lives under the workspace's reports base (stable across all source
        types), never `source/../reports` which breaks virtual/local_path layouts."""
        workspace = self.repository.find_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        return Path(workspace.get_reports_base_dir()) / "code_facts" / "index.json"

    def index_code_facts(self, workspace_id: str) -> Dict[str, Any]:
        """Extract and persist a code-facts index for triage context lookups."""
        workspace_path = self.repository.get_valid_workspace_path(workspace_id)
        workspace_dir = Path(workspace_path)
        if not workspace_dir.exists():
            return {"status": "error", "error": "Workspace path does not exist"}

        result = self.linguist_client.index_code_facts(str(workspace_dir))

        facts_path = self._facts_path(workspace_id)
        facts_path.parent.mkdir(parents=True, exist_ok=True)
        with open(facts_path, "w") as f:
            json.dump(result["facts"], f)
        logger.info(f"Code-facts index persisted: {len(result['facts'])} symbols → {facts_path}")

        return {
            "status": "success",
            "workspace_id": workspace_id,
            "total_symbols": result["total_symbols"],
            "facts_path": str(facts_path),
        }

    def query_code_facts(
        self, workspace_id: str, file: str = None, kind: str = None, name: str = None
    ) -> Dict[str, Any]:
        """Query persisted code-facts index for quick triage context."""
        facts_path = self._facts_path(workspace_id)

        if not facts_path.exists():
            return {"status": "error", "error": "No code-facts index. Run index_code_facts first."}

        with open(facts_path) as f:
            facts = json.load(f)

        if file:
            facts = [s for s in facts if s.get("file") and file in s["file"]]
        if kind:
            facts = [s for s in facts if s.get("kind") == kind]
        if name:
            name_lower = name.lower()
            facts = [s for s in facts if s.get("name") and name_lower in s["name"].lower()]

        return {"status": "success", "matches": len(facts), "symbols": facts[:200]}
