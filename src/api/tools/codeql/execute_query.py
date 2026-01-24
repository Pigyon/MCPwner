"""Execute CodeQL query tool with context enrichment."""

import subprocess
import json
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List
from deps import get_codeql_service, get_workspace_service
from context.sqlite.context_repository import SQLiteContextRepository


def execute_query(
    workspace_id: str,
    database_id: str,
    query_pack: str = "security-extended",
    query_name: str = None,
    query_type: str = "builtin",
    custom_query: str = None,
    enrich_context: bool = True
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
            return {
                "status": "error",
                "error": f"Database not found: {database_id}"
            }
        
        db_path = database.get("path")
        if not db_path:
            return {
                "status": "error",
                "error": "Database path not found in metadata"
            }
        
        # Handle custom query execution
        if query_type == "custom":
            if not custom_query:
                return {
                    "status": "error",
                    "error": "custom_query is required when query_type='custom'"
                }
            
            return _execute_custom_query(
                workspace_id=workspace_id,
                database_id=database_id,
                db_path=db_path,
                custom_query=custom_query,
                enrich_context=enrich_context
            )
        
        # Create temporary SARIF output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sarif', delete=False) as f:
            sarif_output = f.name
        
        try:
            # Build CodeQL analyze command
            cmd = [
                "codeql", "database", "analyze",
                db_path,
                f"codeql/{query_pack}",
                "--format=sarif-latest",
                f"--output={sarif_output}",
                "--sarif-add-snippets"
            ]
            
            if query_name:
                cmd.append(f"--query={query_name}")
            
            # Execute with timeout
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode != 0:
                return {
                    "status": "error",
                    "error": f"Query execution failed: {result.stderr}",
                    "duration_seconds": round(duration, 2)
                }
            
            # Parse SARIF output
            with open(sarif_output, 'r', encoding='utf-8') as f:
                sarif_data = json.load(f)
            
            # Extract findings
            findings = parse_sarif(sarif_data, workspace_id)
            
            # Enrich with function context if requested
            if enrich_context:
                context_db_path = f"/workspaces/{workspace_id}/context.db"
                if Path(context_db_path).exists():
                    findings = enrich_findings_with_context(findings, context_db_path)
            
            # Enforce 10MB result size limit
            result_json = json.dumps(findings)
            if len(result_json) > 10 * 1024 * 1024:
                return {
                    "status": "error",
                    "error": "Results exceed 10MB size limit",
                    "finding_count": len(findings),
                    "duration_seconds": round(duration, 2)
                }
            
            return {
                "status": "success",
                "workspace_id": workspace_id,
                "database_id": database_id,
                "query_pack": query_pack,
                "finding_count": len(findings),
                "findings": findings,
                "duration_seconds": round(duration, 2)
            }
            
        finally:
            # Cleanup temporary file
            Path(sarif_output).unlink(missing_ok=True)
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": "Query execution timed out after 10 minutes"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


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
        tool_name = run.get("tool", {}).get("driver", {}).get("name", "CodeQL")
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
                "help": rule.get("help", {}).get("text", "")
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
        return path[len(prefix):]
    
    # Remove /workspaces/ prefix
    if path.startswith("/workspaces/"):
        parts = path.split("/", 3)
        if len(parts) > 3:
            return parts[3]
    
    return path


def enrich_findings_with_context(
    findings: List[Dict[str, Any]],
    context_db_path: str
) -> List[Dict[str, Any]]:
    """
    Enrich findings with function context from context database.
    
    Args:
        findings: List of finding dictionaries
        context_db_path: Path to context database
        
    Returns:
        Enriched findings list
    """
    repo = SQLiteContextRepository(context_db_path)
    
    for finding in findings:
        file = finding.get("file")
        line = finding.get("start_line")
        
        if file and line:
            try:
                function = repo.code_elements.get_by_location(file, line)
                if function:
                    finding["function_context"] = {
                        "name": function.name,
                        "qualified_name": function.qualified_name,
                        "start_line": function.start_line,
                        "end_line": function.end_line,
                        "code": function.code
                    }
            except Exception:
                # Skip context enrichment on error
                pass
    
    return findings


def _execute_custom_query(
    workspace_id: str,
    database_id: str,
    db_path: str,
    custom_query: str,
    enrich_context: bool
) -> Dict[str, Any]:
    """
    Execute a custom CodeQL query.
    
    Args:
        workspace_id: Workspace ID
        database_id: Database ID
        db_path: Path to CodeQL database
        custom_query: Custom query code
        enrich_context: Whether to enrich with context
        
    Returns:
        Query results dictionary
    """
    # Write custom query to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ql', delete=False) as f:
        query_file = f.name
        f.write(custom_query)
    
    # Create temporary output files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.bqrs', delete=False) as f:
        bqrs_output = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_output = f.name
    
    try:
        start_time = time.time()
        
        # Execute custom query
        cmd = [
            "codeql", "query", "run",
            query_file,
            "--database", db_path,
            "--output", bqrs_output,
            "--threads", "0"  # Use all available threads
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            return {
                "status": "error",
                "error": f"Custom query execution failed: {result.stderr}",
                "duration_seconds": round(time.time() - start_time, 2)
            }
        
        # Decode results to CSV
        decode_cmd = [
            "codeql", "bqrs", "decode",
            bqrs_output,
            "--format=csv",
            "--output", csv_output
        ]
        
        decode_result = subprocess.run(
            decode_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if decode_result.returncode != 0:
            return {
                "status": "error",
                "error": f"Failed to decode query results: {decode_result.stderr}",
                "duration_seconds": round(time.time() - start_time, 2)
            }
        
        # Parse CSV results
        findings = _parse_custom_query_csv(csv_output, workspace_id)
        
        # Enrich with context if requested
        if enrich_context:
            context_db_path = f"/workspaces/{workspace_id}/context.db"
            if Path(context_db_path).exists():
                findings = enrich_findings_with_context(findings, context_db_path)
        
        duration = time.time() - start_time
        
        # Enforce 10MB result size limit
        result_json = json.dumps(findings)
        if len(result_json) > 10 * 1024 * 1024:
            return {
                "status": "error",
                "error": "Results exceed 10MB size limit",
                "finding_count": len(findings),
                "duration_seconds": round(duration, 2)
            }
        
        return {
            "status": "success",
            "workspace_id": workspace_id,
            "database_id": database_id,
            "query_type": "custom",
            "finding_count": len(findings),
            "findings": findings,
            "duration_seconds": round(duration, 2)
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": "Custom query execution timed out after 10 minutes"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
    finally:
        # Cleanup temporary files
        Path(query_file).unlink(missing_ok=True)
        Path(bqrs_output).unlink(missing_ok=True)
        Path(csv_output).unlink(missing_ok=True)


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
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Sanitize file paths if present
                if 'file' in row:
                    row['file'] = sanitize_path(row['file'], workspace_id)
                
                findings.append(dict(row))
    except Exception as e:
        # Return empty list on parse error
        pass
    
    return findings
