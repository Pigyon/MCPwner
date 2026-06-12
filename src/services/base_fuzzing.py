"""Base service for source-fuzzing operations."""

import logging

from clients.base import BaseFuzzingClient
from config.tools import ToolCategory
from repositories.workspace import WorkspaceRepository
from services.base_scan import BaseScanService

logger = logging.getLogger(__name__)


class BaseFuzzingService(BaseScanService):
    """Base service for source-fuzzing operations.

    Source fuzzers (Atheris, Jazzer, Jazzer.js, PHP-Fuzzer) run a white-box,
    coverage-guided fuzzing campaign against a per-target harness inside the
    workspace source tree. They reuse the category-agnostic scan/report logic in
    :class:`BaseScanService` unchanged; only the report category differs. Like
    SAST, the engines are language-specific, so ``fuzzing_list_tools`` filters
    them by detected language — but that filtering lives in the MCP tool layer,
    not here.
    """

    def __init__(self, repository: WorkspaceRepository, client: BaseFuzzingClient):
        super().__init__(repository, client)
        self.tool_category = ToolCategory.FUZZING.value
