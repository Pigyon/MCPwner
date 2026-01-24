"""CodeQL command execution."""

import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CodeQLExecutor:
    """Handles CodeQL command execution."""
    
    def __init__(self, codeql_bin: str = "codeql"):
        self.codeql_bin = codeql_bin
    
    def execute_query(
        self,
        database_path: str,
        query_text: str,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute a CodeQL query and return results.
        
        Args:
            database_path: Path to CodeQL database
            query_text: CodeQL query string
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with:
                - success: bool
                - output_file: str (path to CSV output if success)
                - error: str (error message if failed)
        """
        # Create temporary query file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ql', delete=False) as f:
            f.write(query_text)
            query_file = f.name
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name
        
        try:
            # Execute CodeQL query
            cmd = [
                self.codeql_bin, "query", "run",
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
                timeout=timeout
            )
            
            if result.returncode != 0:
                logger.error(f"CodeQL query failed: {result.stderr}")
                Path(query_file).unlink(missing_ok=True)
                Path(output_file).unlink(missing_ok=True)
                return {
                    "success": False,
                    "error": f"CodeQL query failed: {result.stderr}"
                }
            
            # Cleanup query file but keep output
            Path(query_file).unlink(missing_ok=True)
            
            return {
                "success": True,
                "output_file": output_file
            }
            
        except subprocess.TimeoutExpired:
            logger.error("CodeQL query timed out")
            Path(query_file).unlink(missing_ok=True)
            Path(output_file).unlink(missing_ok=True)
            return {
                "success": False,
                "error": f"Query execution timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"CodeQL execution failed: {e}")
            Path(query_file).unlink(missing_ok=True)
            Path(output_file).unlink(missing_ok=True)
            return {
                "success": False,
                "error": str(e)
            }
