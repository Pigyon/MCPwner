"""
Abstract base class for security analysis tool managers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class ToolManager(ABC):
    """
    Abstract base class for managing security analysis tools.
    
    Provides a common interface for tool availability checking, version
    retrieval, scan execution, and result parsing.
    """
    
    @abstractmethod
    def check_availability(self) -> bool:
        """
        Check if the tool is available and accessible.
        
        Returns:
            True if tool is available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_version(self) -> Optional[str]:
        """
        Get the tool version.
        
        Returns:
            Version string if available, None otherwise
        """
        pass
    
    @abstractmethod
    def execute_scan(
        self,
        workspace_id: str,
        scan_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a security scan.
        
        Args:
            workspace_id: UUID of the workspace to scan
            scan_config: Tool-specific scan configuration
            
        Returns:
            Scan results dictionary
        """
        pass
    
    @abstractmethod
    def parse_results(self, raw_results: Any) -> Dict[str, Any]:
        """
        Parse raw tool output into structured format.
        
        Args:
            raw_results: Raw output from the tool
            
        Returns:
            Structured results dictionary
        """
        pass
