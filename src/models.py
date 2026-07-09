"""Domain models for MCPwner using Pydantic."""

from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import PlainSerializer

IsoDateTime = Annotated[
    datetime,
    PlainSerializer(lambda v: v.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z", return_type=str),
]


class Workspace(PydanticBaseModel):
    """Workspace domain model."""

    workspace_id: str
    source_type: str
    source: str
    created_at: IsoDateTime
    path: Optional[str] = None
    local_path: Optional[str] = None
    mount_path: Optional[str] = None
    workspace_base_dir: Optional[str] = None

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


class CodeQLDatabase(PydanticBaseModel):
    """CodeQL database domain model."""

    database_id: str
    workspace_id: str
    language: str
    created_at: IsoDateTime
    path: str
    status: str = "ready"  # ready, creating, failed
    error: Optional[str] = None
