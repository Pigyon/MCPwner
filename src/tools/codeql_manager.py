"""
CodeQL tool manager for database creation and query execution.
Communicates with CodeQL service via HTTP API.
"""

import requests
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from .tool_manager import ToolManager


class CodeQLManager(ToolManager):
    """
    Manages CodeQL operations including availability checks, language detection,
    database creation, and query execution.
    """
    
    # Supported CodeQL languages with their file extensions
    LANGUAGE_EXTENSIONS = {
        "python": [".py"],
        "javascript": [".js", ".jsx", ".mjs", ".cjs"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "cpp": [".cpp", ".cc", ".cxx", ".c", ".h", ".hpp"],
        "csharp": [".cs"],
        "go": [".go"],
        "ruby": [".rb"],
        "swift": [".swift"],
        "kotlin": [".kt", ".kts"],
        "rust": [".rs"]
    }
    
    def __init__(self, service_url: str = None):
        """
        Initialize CodeQL manager.
        
        Args:
            service_url: URL of the CodeQL HTTP service (defaults to env var CODEQL_SERVICE_URL)
        """
        self.service_url = service_url or os.getenv("CODEQL_SERVICE_URL", "http://codeql:8080")
        self.timeout = 30  # Default timeout for API calls
    
    def check_availability(self) -> bool:
        """
        Check if CodeQL service is available.
        
        Returns:
            True if CodeQL is accessible, False otherwise
        """
        try:
            response = requests.get(
                f"{self.service_url}/health",
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_version(self) -> Optional[str]:
        """
        Get CodeQL version from the service.
        
        Returns:
            Version string if available, None otherwise
        """
        try:
            response = requests.get(
                f"{self.service_url}/version",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("version", "unknown")
            return None
        except Exception:
            return None
    
    def detect_languages(self, workspace_path: str) -> List[str]:
        """
        Detect programming languages in a workspace by scanning file extensions.
        
        Args:
            workspace_path: Path to the workspace directory
            
        Returns:
            List of detected language names (e.g., ["python", "javascript"])
        """
        workspace = Path(workspace_path)
        if not workspace.exists():
            return []
        
        detected = set()
        
        # Scan all files in workspace
        for file_path in workspace.rglob("*"):
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                
                # Check against language extensions
                for language, extensions in self.LANGUAGE_EXTENSIONS.items():
                    if suffix in extensions:
                        detected.add(language)
        
        return sorted(list(detected))

    def create_database(
        self,
        workspace_id: str,
        language: str,
        workspace_path: str,
        base_path: str = "/workspaces"
    ) -> Dict[str, Any]:
        """
        Create a CodeQL database for a workspace via HTTP API.
        
        Args:
            workspace_id: UUID of the workspace
            language: Programming language for the database
            workspace_path: Path to the source code
            base_path: Base directory for workspaces
            
        Returns:
            Dictionary with database metadata:
                - database_id: Unique identifier
                - language: Programming language
                - created_at: ISO 8601 timestamp
                - path: Path to database directory
                
        Raises:
            ValueError: If language is not supported or workspace not found
            RuntimeError: If database creation fails
        """
        # Validate language
        if language not in self.LANGUAGE_EXTENSIONS:
            raise ValueError(f"Unsupported language: {language}")
        
        # Validate workspace path
        workspace = Path(workspace_path)
        if not workspace.exists():
            raise ValueError(f"Workspace not found: {workspace_path}")
        
        # Create database directory path
        db_path = f"{base_path}/{workspace_id}/databases/{language}"
        
        # Prepare request payload
        payload = {
            "workspace_id": workspace_id,
            "language": language,
            "source_path": workspace_path,
            "db_path": db_path
        }
        
        try:
            # Call CodeQL service API
            response = requests.post(
                f"{self.service_url}/database/create",
                json=payload,
                timeout=600  # 10 minute timeout
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise RuntimeError(f"Database creation failed: {error_data.get('error', 'Unknown error')}")
            
            # Return database metadata from response
            return response.json()
            
        except requests.exceptions.Timeout:
            raise RuntimeError("Database creation timed out after 10 minutes")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Database creation error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Database creation error: {str(e)}")
    
    def execute_scan(
        self,
        workspace_id: str,
        scan_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a CodeQL query scan.
        
        Args:
            workspace_id: UUID of the workspace
            scan_config: Configuration including database_id, query_type, and query
            
        Returns:
            Scan results dictionary
        """
        # Placeholder for Phase 10 implementation
        return {
            "status": "not_implemented",
            "message": "Query execution will be implemented in Phase 10"
        }
    
    def parse_results(self, raw_results: Any) -> Dict[str, Any]:
        """
        Parse CodeQL SARIF output into structured format.
        
        Args:
            raw_results: Raw SARIF output from CodeQL
            
        Returns:
            Structured results dictionary
        """
        # Placeholder for Phase 10 implementation
        return {
            "status": "not_implemented",
            "message": "Result parsing will be implemented in Phase 10"
        }
