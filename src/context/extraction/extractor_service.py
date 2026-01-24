"""Service for extracting code context from CodeQL databases."""

import time
import logging
from typing import Dict, Any
from ..adapters import get_adapter
from ..models import CodeElement, CallRelationship
from ..sqlite.context_repository import SQLiteContextRepository
from .codeql_executor import CodeQLExecutor
from .csv_parser import parse_csv_results

logger = logging.getLogger(__name__)


class ContextExtractorService:
    """Service for extracting code context from CodeQL."""
    
    def __init__(self, codeql_bin: str = "codeql"):
        self.executor = CodeQLExecutor(codeql_bin)
    
    def extract_functions(
        self,
        database_path: str,
        context_db_path: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Extract functions from CodeQL database into context database.
        
        Args:
            database_path: Path to CodeQL database
            context_db_path: Path to context SQLite database
            language: Programming language
            
        Returns:
            Dictionary with extraction statistics
        """
        start_time = time.time()
        
        # Initialize repository
        repo = SQLiteContextRepository(context_db_path)
        repo.initialize()
        
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
        
        # Execute CodeQL query
        query_text = adapter.get_functions_query()
        result = self.executor.execute_query(database_path, query_text)
        
        if not result["success"]:
            return {
                "status": "error",
                "error": result["error"],
                "functions_extracted": 0,
                "duration_seconds": time.time() - start_time
            }
        
        # Parse results
        parsed_rows = parse_csv_results(
            result["output_file"],
            adapter.parse_function_result
        )
        
        # Convert to CodeElement objects
        elements = [
            CodeElement(
                id=None,
                element_type='function',
                name=row['name'],
                qualified_name=row.get('qualified_name'),
                file=row['file'],
                start_line=row['start_line'],
                end_line=row['end_line'],
                code=row.get('code', ''),
                language=language,
                metadata=None
            )
            for row in parsed_rows
        ]
        
        # Bulk insert into context database
        count = repo.code_elements.bulk_add(elements)
        
        duration = time.time() - start_time
        logger.info(f"Extracted {count} functions in {duration:.1f}s")
        
        return {
            "status": "success",
            "functions_extracted": count,
            "duration_seconds": round(duration, 2)
        }
    
    def extract_call_graph(
        self,
        database_path: str,
        context_db_path: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Extract call graph from CodeQL database into context database.
        
        Args:
            database_path: Path to CodeQL database
            context_db_path: Path to context SQLite database
            language: Programming language
            
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
        
        # Execute CodeQL query
        query_text = adapter.get_call_graph_query()
        result = self.executor.execute_query(database_path, query_text)
        
        if not result["success"]:
            return {
                "status": "error",
                "error": result["error"],
                "relationships_extracted": 0,
                "duration_seconds": time.time() - start_time
            }
        
        # Parse results
        parsed_rows = parse_csv_results(
            result["output_file"],
            adapter.parse_call_graph_result
        )
        
        # Build call relationships
        relationships_count = 0
        repo = SQLiteContextRepository(context_db_path)
        
        for row in parsed_rows:
            try:
                # Find caller and callee
                caller = repo.code_elements.get_by_name(
                    row['caller_name'],
                    row['caller_file']
                )
                callee = repo.code_elements.get_by_name(
                    row['callee_name'],
                    row['callee_file']
                )
                
                if caller and callee:
                    relationship = CallRelationship(
                        id=None,
                        caller_id=caller.id,
                        callee_id=callee.id,
                        call_site_line=row.get('call_line')
                    )
                    repo.call_graph.add(relationship)
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
