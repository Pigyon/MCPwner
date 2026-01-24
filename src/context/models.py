"""Domain models for code context.

Re-exports from main models module for backward compatibility.
"""

from models import CallRelationship, CodeElement

__all__ = ["CodeElement", "CallRelationship"]
