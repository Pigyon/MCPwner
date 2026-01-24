"""Code context extraction using CodeQL."""

import csv
import subprocess
import tempfile
import time
import logging
from pathlib import Path
from typing import Dict, Any, List
from context.adapters import get_adapter
from context.sqlite.operations import get_connection, bulk_insert_code_elements, insert_call_relationship
from context.sqlite.schema import init_context_db

logger = logging.getLogger(__name__)


def extract_functions(
    database_path: str,
    context_db_path: str,
    language: str,
    codeql_bin: str = "codeql"
) -> Dict[str, Any]:
    """
    Extract functions from CodeQL database into context database.
    
    Args:
        database_path: Path to CodeQL database
        context_db_path: Path to context SQLite database
        language: Programming language
        codeql_bin: Path to CodeQL binary (default: "codeql")
        
    Returns:
        Dictionary with extraction statistics:
            - functions_extracted: Number of functions extracted
            - duration_seconds: Time taken
            - status: "success" or "error"
            
    Raises:
        ValueError: If language is not supported
        RuntimeError: If CodeQL query execution fails
    """
    start_time = time.time()
    
    # Initialize context database if needed
    init_context_db(context_db_path)
    
    # Get language adapter
    try:
        adapter = get_adapter(language)
    except ValueError as e:
        return {
            "status": "error",
            "error": str(e),
            "functions_extracted": 0,
            "duration_seconds": 0
        }
    
    # Get CodeQL query
    query_text = adapter.get_functions_query()
    
    # Create temporary query file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ql', delete=False) as f:
        f.write(query_text)
        query_file = f.name
    
    try:
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name
        
        # Execute CodeQL query
        cmd = [
            codeql_bin, "query", "run",
            f"--database={database_path}",
            f"--output={output_file}",
            "--format=csv",
            query_file
        ]
        
        logger.info(f"Executing CodeQL query: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"CodeQL query failed: {result.stderr}")
            return {
                "status": "error",
                "error": f"CodeQL query failed: {result.stderr}",
                "functions_extracted": 0,
                "duration_seconds": time.time() - start_time
            }
        
        # Parse CSV output
        elements = []
        with open(output_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # Skip header
            
            for row in reader:
                try:
                    parsed = adapter.parse_function_result(row)
                    elements.append({
                        'element_type': 'function',
                        'name': parsed['name'],
                        'qualified_name': parsed.get('qualified_name'),
                        'file': parsed['file'],
                        'start_line': parsed['start_line'],
                        'end_line': parsed['end_line'],
                        'code': parsed.get('code', ''),
                        'language': language,
                        'metadata': None
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse row: {row}, error: {e}")
                    continue
        
        # Bulk insert into context database
        with get_connection(context_db_path) as conn:
            count = bulk_insert_code_elements(conn, elements)
        
        duration = time.time() - start_time
        logger.info(f"Extracted {count} functions in {duration:.1f}s")
        
        return {
            "status": "success",
            "functions_extracted": count,
            "duration_seconds": round(duration, 2)
        }
        
    except subprocess.TimeoutExpired:
        logger.error("CodeQL query timed out")
        return {
            "status": "error",
            "error": "Query execution timed out after 5 minutes",
            "functions_extracted": 0,
            "duration_seconds": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"Function extraction failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "functions_extracted": 0,
            "duration_seconds": time.time() - start_time
        }
    finally:
        # Cleanup temporary files
        try:
            Path(query_file).unlink(missing_ok=True)
            Path(output_file).unlink(missing_ok=True)
        except Exception:
            pass


def extract_call_graph(
    database_path: str,
    context_db_path: str,
    language: str,
    codeql_bin: str = "codeql"
) -> Dict[str, Any]:
    """
    Extract call graph from CodeQL database into context database.
    
    Args:
        database_path: Path to CodeQL database
        context_db_path: Path to context SQLite database
        language: Programming language
        codeql_bin: Path to CodeQL binary (default: "codeql")
        
    Returns:
        Dictionary with extraction statistics
    """
    start_time = time.time()
    
    # Get language adapter
    try:
        adapter = get_adapter(language)
    except ValueError as e:
        return {
            "status": "error",
            "error": str(e),
            "relationships_extracted": 0,
            "duration_seconds": 0
        }
    
    # Get CodeQL query
    query_text = adapter.get_call_graph_query()
    
    # Create temporary query file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ql', delete=False) as f:
        f.write(query_text)
        query_file = f.name
    
    try:
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name
        
        # Execute CodeQL query
        cmd = [
            codeql_bin, "query", "run",
            f"--database={database_path}",
            f"--output={output_file}",
            "--format=csv",
            query_file
        ]
        
        logger.info(f"Executing call graph query: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Call graph query failed: {result.stderr}")
            return {
                "status": "error",
                "error": f"Call graph query failed: {result.stderr}",
                "relationships_extracted": 0,
                "duration_seconds": time.time() - start_time
            }
        
        # Parse CSV output and build call relationships
        relationships_count = 0
        with get_connection(context_db_path) as conn:
            cursor = conn.cursor()
            
            with open(output_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip header
                
                for row in reader:
                    try:
                        parsed = adapter.parse_call_graph_result(row)
                        
                        # Find caller and callee IDs
                        cursor.execute(
                            "SELECT id FROM code_elements WHERE name = ? AND file = ? LIMIT 1",
                            (parsed['caller_name'], parsed['caller_file'])
                        )
                        caller_row = cursor.fetchone()
                        
                        cursor.execute(
                            "SELECT id FROM code_elements WHERE name = ? AND file = ? LIMIT 1",
                            (parsed['callee_name'], parsed['callee_file'])
                        )
                        callee_row = cursor.fetchone()
                        
                        if caller_row and callee_row:
                            insert_call_relationship(
                                conn,
                                caller_row[0],
                                callee_row[0],
                                parsed.get('call_line')
                            )
                            relationships_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to process call relationship: {e}")
                        continue
        
        duration = time.time() - start_time
        logger.info(f"Extracted {relationships_count} call relationships in {duration:.1f}s")
        
        return {
            "status": "success",
            "relationships_extracted": relationships_count,
            "duration_seconds": round(duration, 2)
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": "Call graph extraction timed out after 5 minutes",
            "relationships_extracted": 0,
            "duration_seconds": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"Call graph extraction failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "relationships_extracted": 0,
            "duration_seconds": time.time() - start_time
        }
    finally:
        # Cleanup temporary files
        try:
            Path(query_file).unlink(missing_ok=True)
            Path(output_file).unlink(missing_ok=True)
        except Exception:
            pass
