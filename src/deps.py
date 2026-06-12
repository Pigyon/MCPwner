"""Dependency management for MCPwner.

Clients and services for the registry-driven scan tools (SAST / SCA / Secrets /
Reconnaissance) are built generically from :data:`config.tools.TOOL_REGISTRY`
by :func:`get_client` / :func:`get_service`. CodeQL, Linguist and the workspace
layer have bespoke wiring and stay as explicit factories below.
"""

from functools import lru_cache
from typing import Any

from clients.base import (
    BaseFuzzingClient,
    BaseIaCClient,
    BaseSASTClient,
    BaseScanClient,
    BaseSCAClient,
)
from clients.base_reconnaissance import BaseReconnaissanceClient
from clients.base_secrets import BaseSecretsClient
from clients.base_utilities import BaseUtilitiesClient
from clients.codeql import CodeQLClient
from clients.linguist import LinguistClient
from config.config import load_config
from config.tools import TOOL_REGISTRY, ToolSpec
from repositories.workspace import WorkspaceRepository
from services.base_fuzzing import BaseFuzzingService
from services.base_iac import BaseIaCService
from services.base_reconnaissance import BaseReconnaissanceService
from services.base_sast import BaseSASTService
from services.base_sca import BaseSCAService
from services.base_scan import BaseScanService
from services.base_secrets import BaseSecretsService
from services.base_utilities import BaseUtilitiesService
from services.codeql import CodeQLService
from services.linguist import LinguistService
from services.workspace import WorkspaceService


@lru_cache(maxsize=None)
def get_config():
    """Get configuration singleton."""
    return load_config("config/config.yaml")


@lru_cache(maxsize=None)
def get_workspace_repository():
    """Get workspace repository singleton."""
    return WorkspaceRepository()


# ---------------------------------------------------------------------------
# Registry-driven clients and services
# ---------------------------------------------------------------------------

_CLIENT_BASES = {
    "sast": BaseSASTClient,
    "sca": BaseSCAClient,
    "secrets": BaseSecretsClient,
    "reconnaissance": BaseReconnaissanceClient,
    "utilities": BaseUtilitiesClient,
    "iac": BaseIaCClient,
    "fuzzing": BaseFuzzingClient,
}

_SERVICE_BASES = {
    "sast": BaseSASTService,
    "sca": BaseSCAService,
    "secrets": BaseSecretsService,
    "reconnaissance": BaseReconnaissanceService,
    "utilities": BaseUtilitiesService,
    "iac": BaseIaCService,
    "fuzzing": BaseFuzzingService,
}


def _resolve_service_url(spec: ToolSpec) -> str:
    """Resolve a tool's service URL from config, falling back to its default."""
    node: Any = get_config()
    for key in spec.config_path:
        node = node.get(key, {}) if isinstance(node, dict) else {}
    url = node.get("service_url") if isinstance(node, dict) else None
    return url or spec.default_url


@lru_cache(maxsize=None)
def get_client(name: str) -> BaseScanClient:
    """Get the HTTP client singleton for a registry tool."""
    spec = TOOL_REGISTRY[name]
    return _CLIENT_BASES[spec.category](_resolve_service_url(spec), name)


@lru_cache(maxsize=None)
def get_service(name: str) -> BaseScanService:
    """Get the service singleton for a registry tool."""
    spec = TOOL_REGISTRY[name]
    return _SERVICE_BASES[spec.category](get_workspace_repository(), get_client(name))


# ---------------------------------------------------------------------------
# Bespoke wiring: workspace, Linguist, CodeQL
# ---------------------------------------------------------------------------


@lru_cache(maxsize=None)
def get_workspace_service():
    """Get workspace service singleton."""
    return WorkspaceService(get_workspace_repository())


def _bespoke_service_url(section: str, default: str) -> str:
    """Resolve a non-registry tool's service URL from config, falling back to default."""
    node = get_config().get(section, {})
    url = node.get("service_url") if isinstance(node, dict) else None
    return url or default


@lru_cache(maxsize=None)
def get_linguist_client():
    """Get Linguist client singleton."""
    return LinguistClient(_bespoke_service_url("linguist", "http://linguist:8081"))


@lru_cache(maxsize=None)
def get_linguist_service():
    """Get Linguist service singleton."""
    return LinguistService(get_workspace_repository(), get_linguist_client())


@lru_cache(maxsize=None)
def get_codeql_client():
    """Get CodeQL client singleton."""
    return CodeQLClient(_bespoke_service_url("codeql", "http://codeql:8080"))


@lru_cache(maxsize=None)
def get_codeql_service():
    """Get CodeQL service singleton."""
    return CodeQLService(get_workspace_repository(), get_codeql_client(), get_linguist_service())
