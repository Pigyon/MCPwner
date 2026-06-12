"""Base service for Infrastructure-as-Code (IaC) scanning operations."""

import logging

from clients.base import BaseIaCClient
from config.tools import ToolCategory
from repositories.workspace import WorkspaceRepository
from services.base_scan import BaseScanService

logger = logging.getLogger(__name__)


class BaseIaCService(BaseScanService):
    """Base service for IaC scanning operations.

    IaC scanners (Checkov, KICS, Terrascan, TFSec, Hadolint) inspect static
    infrastructure definitions — Terraform, CloudFormation, Kubernetes manifests,
    Dockerfiles, etc. — so they reuse the category-agnostic scan/report logic in
    :class:`BaseScanService` unchanged; only the report category differs.
    """

    def __init__(self, repository: WorkspaceRepository, client: BaseIaCClient):
        super().__init__(repository, client)
        self.tool_category = ToolCategory.IAC.value
