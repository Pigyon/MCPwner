"""Domain models for MCPwner using Pydantic."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer


class Workspace(BaseModel):
    """Workspace domain model."""

    workspace_id: str
    source_type: str  # "github", "local", "local_path", or "virtual"
    source: str
    created_at: datetime
    path: Optional[str] = None
    local_path: Optional[str] = None
    mount_path: Optional[str] = None
    workspace_base_dir: Optional[str] = None  # Base dir for reports/metadata (e.g. /workspaces/{id})

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

    def is_local_path(self) -> bool:
        """Check if workspace points directly to a local codebase."""
        return self.source_type == "local_path"

    def is_virtual(self) -> bool:
        """Check if workspace is virtual (no source code)."""
        return self.source_type == "virtual"

    def get_reports_base_dir(self) -> str:
        """Get the base directory for reports and metadata.

        Returns workspace_base_dir which is always set during workspace creation.
        Falls back to /workspaces/{id} for legacy workspaces created before this field existed.
        """
        if self.workspace_base_dir:
            return self.workspace_base_dir
        # Legacy fallback for workspaces persisted before workspace_base_dir was added
        return f"/workspaces/{self.workspace_id}"


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
