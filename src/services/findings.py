"""Findings ledger - persistent store for security findings in a workspace.

One JSON file per finding under the workspace volume (<reports_base>/findings/F-NNN.json),
so it survives restarts and can always be re-read later in an assessment.
Findings are free-form (only `id` is required); a caller may own different
sub-objects of the same finding (e.g. `poc`, `review`), so `upsert_finding`
deep-merges by default instead of clobbering previously written fields.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from repositories.workspace import WorkspaceRepository

logger = logging.getLogger(__name__)

# A finding id becomes a filename, so it must be a safe, traversal-proof token.
_FINDING_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Lets one agent update e.g. `poc` without wiping a peer's `review`."""
    merged = dict(base)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class FindingsService:
    """Workspace-scoped CRUD for the findings ledger — local file I/O, no client/container."""

    def __init__(self, workspace_repository: WorkspaceRepository):
        self.workspace_repository = workspace_repository

    def _findings_dir(self, workspace_id: str) -> Path:
        workspace = self.workspace_repository.find_by_id(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        findings_dir = Path(workspace.get_reports_base_dir()) / "findings"
        findings_dir.mkdir(parents=True, exist_ok=True)
        return findings_dir

    def _finding_path(self, workspace_id: str, finding_id: str) -> Path:
        if not finding_id or not _FINDING_ID_RE.match(finding_id):
            raise ValueError(
                f"Invalid finding id '{finding_id}': must match {_FINDING_ID_RE.pattern} (e.g. 'F-001')."
            )
        return self._findings_dir(workspace_id) / f"{finding_id}.json"

    @staticmethod
    def _atomic_write(path: Path, data: Dict[str, Any]) -> None:
        temp_path = path.with_suffix(".json.tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        temp_path.replace(path)

    def upsert_finding(
        self, workspace_id: str, finding: Dict[str, Any], merge: bool = True
    ) -> Dict[str, Any]:
        if not isinstance(finding, dict):
            raise ValueError("finding must be a JSON object")
        finding_id = finding.get("id")
        if not finding_id:
            raise ValueError("finding must include an 'id' (e.g. 'F-001')")

        path = self._finding_path(workspace_id, finding_id)

        stored = finding
        if merge and path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if isinstance(existing, dict):
                    stored = _deep_merge(existing, finding)
            except Exception as e:
                logger.warning(
                    f"Could not read existing finding {finding_id} for merge (overwriting): {e}"
                )

        self._atomic_write(path, stored)
        logger.info(f"Upserted finding {finding_id} in workspace {workspace_id}")
        return stored

    def list_findings(self, workspace_id: str, status: Optional[str] = None) -> Dict[str, Any]:
        """A corrupt finding file is skipped (logged), not a hard failure."""
        findings_dir = self._findings_dir(workspace_id)
        findings: List[Dict[str, Any]] = []
        for finding_path in sorted(findings_dir.glob("*.json")):
            try:
                with open(finding_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.warning(f"Skipping unparseable finding {finding_path.name}: {e}")
                continue
            if status and isinstance(data, dict) and data.get("status") != status:
                continue
            findings.append(data)
        return {"workspace_id": workspace_id, "count": len(findings), "findings": findings}

    def get_finding(self, workspace_id: str, finding_id: str) -> Optional[Dict[str, Any]]:
        path = self._finding_path(workspace_id, finding_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
