"""Execute CodeQL query tool."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from api.tools.common import handle_tool_error
from deps import get_codeql_service, get_workspace_repository

logger = logging.getLogger(__name__)

# Maximum serialized size of query results returned to the LLM.
MAX_RESULT_BYTES = 10 * 1024 * 1024

# CodeQL often exceeds the 50s MCP timeout; poll the shared SARIF path up to 600s.
QUERY_BACKGROUND_WAIT_SECONDS = 600
QUERY_POLL_INTERVAL_SECONDS = 3


@handle_tool_error
def execute_query(
    workspace_id: str,
    database_id: str,
    query_pack: str = "security-extended",
    query_type: str = "builtin",
    custom_query: Optional[str] = None,
) -> dict:
    """
    Execute CodeQL query on database.

    Args:
        workspace_id: UUID of the workspace
        database_id: ID of the CodeQL database
        query_pack: Query pack name (default: "security-extended")
        query_type: Type of query - "builtin" or "custom" (default: "builtin")
        custom_query: Custom CodeQL query code (required if query_type="custom")

    Returns:
        Dictionary with query results and findings
    """
    try:
        codeql_service = get_codeql_service()

        if custom_query:
            logger.debug(f"Custom query provided (length: {len(custom_query)})")

        if query_type == "custom":
            return {
                "status": "error",
                "error": "Custom queries are not currently supported in this environment configuration.",
            }

        sarif_filename = f"{workspace_id}_{database_id}_{int(time.time())}.sarif"
        repo = get_workspace_repository()
        ws = repo.find_by_id(workspace_id)
        ws_path = ws.path if ws else None
        reports_base = ws.get_reports_base_dir() if ws else f"/workspaces/{workspace_id}"
        sarif_output = f"{reports_base}/{sarif_filename}"

        try:
            start_time = time.time()

            logger.info(f"Executing query pack {query_pack} via CodeQL service")

            exec_result = codeql_service.execute_query(
                workspace_id=workspace_id,
                database_id=database_id,
                query_pack=query_pack,
                output_path=sarif_output,
            )

            if not Path(sarif_output).exists():
                backgrounded = (
                    isinstance(exec_result, dict) and exec_result.get("status") == "backgrounded"
                )
                wait_timeout = QUERY_BACKGROUND_WAIT_SECONDS if backgrounded else 30
                logger.info(
                    f"SARIF not yet present; polling up to {wait_timeout}s (backgrounded={backgrounded})"
                )
                deadline = time.time() + wait_timeout
                while time.time() < deadline:
                    if Path(sarif_output).exists():
                        break
                    time.sleep(QUERY_POLL_INTERVAL_SECONDS)

            duration = time.time() - start_time

            if not Path(sarif_output).exists():
                return {
                    "status": "error",
                    "error": (
                        f"SARIF output file was not created at {sarif_output}. "
                        f"The query may still be running after {round(duration)}s."
                    ),
                    "duration_seconds": round(duration, 2),
                }

            # Retry briefly: backgrounded queries may land mid-write.
            sarif_data = None
            for attempt in range(5):
                try:
                    with open(sarif_output, "r", encoding="utf-8") as f:
                        sarif_data = json.load(f)
                    break
                except json.JSONDecodeError:
                    if attempt == 4:
                        raise
                    time.sleep(2)

            findings = parse_sarif(sarif_data, workspace_id, ws_path)

            result_json = json.dumps(findings)
            if len(result_json) > MAX_RESULT_BYTES:
                return {
                    "status": "error",
                    "error": "Results exceed 10MB size limit",
                    "finding_count": len(findings),
                    "duration_seconds": round(duration, 2),
                }

            return {
                "status": "success",
                "workspace_id": workspace_id,
                "database_id": database_id,
                "query_pack": query_pack,
                "finding_count": len(findings),
                "findings": findings,
                "duration_seconds": round(duration, 2),
            }

        finally:
            Path(sarif_output).unlink(missing_ok=True)

    except Exception:
        raise


def parse_sarif(
    sarif_data: Dict[str, Any], workspace_id: str, ws_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Parse SARIF output into structured findings.

    Args:
        sarif_data: SARIF JSON data
        workspace_id: Workspace ID for path sanitization
        ws_path: Optional workspace local path for sanitization

    Returns:
        List of finding dictionaries
    """
    findings = []

    for run in sarif_data.get("runs", []):
        rules = {rule["id"]: rule for rule in run.get("tool", {}).get("driver", {}).get("rules", [])}

        for result in run.get("results", []):
            rule_id = result.get("ruleId", "unknown")
            rule = rules.get(rule_id, {})

            locations = result.get("locations", [])
            if not locations:
                continue

            primary_location = locations[0].get("physicalLocation", {})
            artifact_location = primary_location.get("artifactLocation", {})
            region = primary_location.get("region", {})

            file_path = artifact_location.get("uri", "")
            file_path = sanitize_path(file_path, workspace_id, ws_path)

            finding = {
                "rule_id": rule_id,
                "rule_name": rule.get("name", rule_id),
                "severity": result.get("level", "warning"),
                "message": result.get("message", {}).get("text", ""),
                "file": file_path,
                "start_line": region.get("startLine", 0),
                "end_line": region.get("endLine", 0),
                "start_column": region.get("startColumn", 0),
                "snippet": region.get("snippet", {}).get("text", ""),
                "description": rule.get("shortDescription", {}).get("text", ""),
                "help": rule.get("help", {}).get("text", ""),
            }

            findings.append(finding)

    return findings


def sanitize_path(path: str, workspace_id: str, ws_path: Optional[str] = None) -> str:
    """
    Sanitize file path by removing workspace prefix.

    Args:
        path: Original file path
        workspace_id: Workspace ID
        ws_path: Optional workspace local path

    Returns:
        Sanitized relative path
    """
    if ws_path and path.startswith(ws_path):
        relative = path[len(ws_path) :]
        return relative.lstrip("/")

    prefix = f"/workspaces/{workspace_id}/"
    if path.startswith(prefix):
        return path[len(prefix) :]

    if path.startswith("/workspaces/"):
        parts = path.split("/", 3)
        if len(parts) > 3:
            return parts[3]

    return path
