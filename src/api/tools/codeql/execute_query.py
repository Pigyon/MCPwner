"""Execute CodeQL query tool with context enrichment."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List

from deps import get_codeql_service, get_workspace_service

logger = logging.getLogger(__name__)


def execute_query(
    workspace_id: str,
    database_id: str,
    query_pack: str = "security-extended",
    query_name: str = None,
    query_type: str = "builtin",
    custom_query: str = None,
    enrich_context: bool = True,
) -> dict:
    """
    Execute CodeQL query on database with optional context enrichment.

    Args:
        workspace_id: UUID of the workspace
        database_id: ID of the CodeQL database
        query_pack: Query pack name (default: "security-extended")
        query_name: Optional specific query name within pack
        query_type: Type of query - "builtin" or "custom" (default: "builtin")
        custom_query: Custom CodeQL query code (required if query_type="custom")
        enrich_context: Whether to enrich findings with function context (default: True)

    Returns:
        Dictionary with query results and findings
    """
    try:
        # Validate workspace
        workspace_service = get_workspace_service()
        workspace = workspace_service.get_workspace(workspace_id)

        # Get database metadata from CodeQL service
        codeql_service = get_codeql_service()
        databases = codeql_service.list_databases(workspace_id)
        database = next((db for db in databases if db.get("database_id") == database_id), None)

        if not database:
            return {"status": "error", "error": f"Database not found: {database_id}"}

        db_path = database.get("path")
        if not db_path:
            return {"status": "error", "error": "Database path not found in metadata"}

        # Handle custom query execution
        if query_type == "custom":
            # For now, custom queries are not fully supported in remote execution mode
            # unless we implement a way to send the query content to the executor
            return {
                "status": "error",
                "error": "Custom queries are not currently supported in this environment configuration.",
            }

        # Create temporary SARIF output file path (in the shared workspace volume)
        # We assume /workspaces is shared between mcpwner and codeql-executor
        sarif_filename = f"{workspace_id}_{database_id}_{int(time.time())}.sarif"
        sarif_output = f"/workspaces/{workspace_id}/{sarif_filename}"

        try:
            start_time = time.time()

            # Execute via CodeQL Service (HTTP to codeql-executor)
            logger.info(f"Executing query pack {query_pack} via CodeQL service")

            # The service call should handle the execution remotely
            # We pass the output_path where we expect the result to be written
            # Since both containers share /workspaces, the executor writes it there, and we read it here.
            codeql_service.execute_query(
                workspace_id=workspace_id,
                database_id=database_id,
                query_pack=query_pack,
                output_path=sarif_output
            )

            duration = time.time() - start_time

            # Check if output file exists
            if not Path(sarif_output).exists():
                return {
                    "status": "error",
                    "error": f"SARIF output file was not created at {sarif_output}",
                    "duration_seconds": round(duration, 2),
                }

            # Parse SARIF output
            with open(sarif_output, "r", encoding="utf-8") as f:
                sarif_data = json.load(f)

            # Extract findings
            findings = parse_sarif(sarif_data, workspace_id)

            # Enrich with function context if requested
            if enrich_context:
                # Context extraction is disabled due to stability issues
                # context_db_path = f"/workspaces/{workspace_id}/context.db"
                # if Path(context_db_path).exists():
                #     findings = enrich_findings_with_context(findings, context_db_path)
                pass

            # Enforce 10MB result size limit
            result_json = json.dumps(findings)
            if len(result_json) > 10 * 1024 * 1024:
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
            # Cleanup temporary file
            Path(sarif_output).unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return {"status": "error", "error": str(e)}


def parse_sarif(sarif_data: Dict[str, Any], workspace_id: str) -> List[Dict[str, Any]]:
    """
    Parse SARIF output into structured findings.

    Args:
        sarif_data: SARIF JSON data
        workspace_id: Workspace ID for path sanitization

    Returns:
        List of finding dictionaries
    """
    findings = []

    for run in sarif_data.get("runs", []):
        _ = run.get("tool", {}).get("driver", {}).get("name", "CodeQL")  # tool_name unused
        rules = {rule["id"]: rule for rule in run.get("tool", {}).get("driver", {}).get("rules", [])}

        for result in run.get("results", []):
            rule_id = result.get("ruleId", "unknown")
            rule = rules.get(rule_id, {})

            # Get primary location
            locations = result.get("locations", [])
            if not locations:
                continue

            primary_location = locations[0].get("physicalLocation", {})
            artifact_location = primary_location.get("artifactLocation", {})
            region = primary_location.get("region", {})

            # Sanitize file path (remove /workspaces/ prefix)
            file_path = artifact_location.get("uri", "")
            file_path = sanitize_path(file_path, workspace_id)

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


def sanitize_path(path: str, workspace_id: str) -> str:
    """
    Sanitize file path by removing workspace prefix.

    Args:
        path: Original file path
        workspace_id: Workspace ID

    Returns:
        Sanitized relative path
    """
    # Remove /workspaces/{workspace_id}/ prefix
    prefix = f"/workspaces/{workspace_id}/"
    if path.startswith(prefix):
        return path[len(prefix) :]

    # Remove /workspaces/ prefix
    if path.startswith("/workspaces/"):
        parts = path.split("/", 3)
        if len(parts) > 3:
            return parts[3]

    return path


# def enrich_findings_with_context(
#     findings: List[Dict[str, Any]], context_db_path: str
# ) -> List[Dict[str, Any]]:
#     """
#     Enrich findings with function context from context database.
#
#     Args:
#         findings: List of finding dictionaries
#         context_db_path: Path to context database
#
#     Returns:
#         Enriched findings list
#     """
#     repo = SQLiteContextRepository(context_db_path)
#
#     for finding in findings:
#         file = finding.get("file")
#         line = finding.get("start_line")
#
#         if file and line:
#             try:
#                 function = repo.code_elements.get_by_location(file, line)
#                 if function:
#                     finding["function_context"] = {
#                         "name": function.name,
#                         "qualified_name": function.qualified_name,
#                         "start_line": function.start_line,
#                         "end_line": function.end_line,
#                         "code": function.code,
#                     }
#             except Exception:
#                 # Skip context enrichment on error
#                 pass
#
#     return findings


def _parse_custom_query_csv(csv_path: str, workspace_id: str) -> List[Dict[str, Any]]:
    """
    Parse CSV output from custom query.

    Args:
        csv_path: Path to CSV file
        workspace_id: Workspace ID for path sanitization

    Returns:
        List of finding dictionaries
    """
    import csv

    findings = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Sanitize file paths if present
                if "file" in row:
                    row["file"] = sanitize_path(row["file"], workspace_id)

                findings.append(dict(row))
    except Exception:
        # Return empty list on parse error
        pass

    return findings
