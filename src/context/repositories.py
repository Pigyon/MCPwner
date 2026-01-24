"""Abstract repository interfaces for code context."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .models import CallRelationship, CodeElement


class CodeElementRepository(ABC):
    """Abstract repository for code elements."""

    @abstractmethod
    def add(self, element: CodeElement) -> int:
        """
        Add a code element.

        Args:
            element: CodeElement to add

        Returns:
            ID of inserted element
        """
        pass

    @abstractmethod
    def bulk_add(self, elements: List[CodeElement]) -> int:
        """
        Add multiple code elements.

        Args:
            elements: List of CodeElements to add

        Returns:
            Number of elements inserted
        """
        pass

    @abstractmethod
    def get_by_id(self, element_id: int) -> Optional[CodeElement]:
        """Get element by ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: str, file: Optional[str] = None) -> Optional[CodeElement]:
        """Get element by name and optional file."""
        pass

    @abstractmethod
    def get_by_location(self, file: str, line: int) -> Optional[CodeElement]:
        """Get element containing a specific line in a file."""
        pass

    @abstractmethod
    def search(
        self,
        name_pattern: Optional[str] = None,
        file_pattern: Optional[str] = None,
        language: Optional[str] = None,
        element_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[CodeElement]:
        """Search for elements with filters."""
        pass

    @abstractmethod
    def clear(self, language: Optional[str] = None) -> int:
        """Clear elements, optionally filtered by language."""
        pass


class CallGraphRepository(ABC):
    """Abstract repository for call graph relationships."""

    @abstractmethod
    def add(self, relationship: CallRelationship) -> int:
        """Add a call relationship."""
        pass

    @abstractmethod
    def get_callers(self, element_id: int) -> List[CodeElement]:
        """Get all elements that call the specified element."""
        pass

    @abstractmethod
    def get_callees(self, element_id: int) -> List[CodeElement]:
        """Get all elements called by the specified element."""
        pass

    @abstractmethod
    def get_callers_by_name(self, function_name: str, file: Optional[str] = None) -> List[CodeElement]:
        """Get callers by function name."""
        pass

    @abstractmethod
    def get_callees_by_name(self, function_name: str, file: Optional[str] = None) -> List[CodeElement]:
        """Get callees by function name."""
        pass


class ContextRepository(ABC):
    """Combined repository interface for context operations."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the repository (create schema, etc.)."""
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics."""
        pass

    @property
    @abstractmethod
    def code_elements(self) -> CodeElementRepository:
        """Access to code element repository."""
        pass

    @property
    @abstractmethod
    def call_graph(self) -> CallGraphRepository:
        """Access to call graph repository."""
        pass
