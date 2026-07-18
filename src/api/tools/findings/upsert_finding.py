"""Upsert (create or update) a finding in the workspace findings ledger."""

from typing import Any, Dict

from api.tools.common import handle_tool_error
from deps import get_findings_service


@handle_tool_error
def upsert_finding(workspace_id: str, finding: Dict[str, Any], merge: bool = True) -> dict:
    """
    Create or update a finding in the workspace findings ledger (a persistent store
    of findings for an assessment). Persisted as ``<workspace>/findings/<id>.json``,
    so it survives restarts and can be re-read later.

    Args:
        workspace_id: UUID of the workspace the finding belongs to.
        finding: The finding as a JSON object. MUST include an ``id`` (e.g. "F-001").
            Follow the ledger schema (see skills/schemas/finding.schema.json): fields
            like status, severity, cwe, discovery_lane, reachability, triage, evidence,
            poc (incl. poc.oracle), review, hypothesis, novelty, priority_score,
            chain_of. Any additional fields are preserved.
        merge: If True (default), deep-merge into the existing entry - so a caller can
            update one sub-object (e.g. ``poc``) without clobbering previously written
            fields (e.g. ``review``). Set False to fully replace the stored entry.

    Returns:
        {"status": "success", "workspace_id", "id", "finding": <stored finding>}
    """
    stored = get_findings_service().upsert_finding(workspace_id, finding, merge=merge)
    return {
        "status": "success",
        "workspace_id": workspace_id,
        "id": stored.get("id"),
        "finding": stored,
    }
