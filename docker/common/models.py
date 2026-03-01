from typing import Any, Dict, Optional

from pydantic import BaseModel


class ScanRequest(BaseModel):
    workspace_path: str
    scan_path: Optional[str] = "."
    config: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    service: str


class VersionResponse(BaseModel):
    version: str
    status: str


class ScanResponse(BaseModel):
    status: str
    finding_count: int
    report_path: str
    error: Optional[str] = None
