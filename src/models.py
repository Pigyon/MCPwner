"""Domain models for MCPwner using Pydantic."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer


class Workspace(BaseModel):
    """Workspace domain model."""

    workspace_id: str
    source_type: str  # "github" or "local"
    source: str
    created_at: datetime
    path: Optional[str] = None
    local_path: Optional[str] = None
    mount_path: Optional[str] = None

    model_config = ConfigDict()

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info):
        return dt.isoformat() + "Z"

    def is_github_clone(self) -> bool:
        """Check if workspace is a GitHub clone."""
        return self.source_type == "github"

    def is_local_mount(self) -> bool:
        """Check if workspace is a local mount."""
        return self.source_type == "local"


class CodeQLDatabase(BaseModel):
    """CodeQL database domain model."""

    database_id: str
    workspace_id: str
    language: str
    created_at: datetime
    path: str
    status: str = "ready"  # ready, creating, failed
    error: Optional[str] = None

    model_config = ConfigDict()

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info):
        return dt.isoformat() + "Z"


class CodeElement(BaseModel):
    """Code element model (function, method, class)."""

    id: Optional[int] = None
    element_type: str  # 'function', 'method', 'class'
    name: str
    qualified_name: Optional[str] = None
    file: str
    start_line: int
    end_line: int
    code: str
    language: str
    metadata: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def to_dict(self):
        """Convert to dictionary for backward compatibility."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary for backward compatibility."""
        return cls(**data)


class CallRelationship(BaseModel):
    """Call relationship between code elements."""

    id: Optional[int] = None
    caller_id: int
    callee_id: int
    call_site_line: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

    def to_dict(self):
        """Convert to dictionary for backward compatibility."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary for backward compatibility."""
        return cls(**data)
