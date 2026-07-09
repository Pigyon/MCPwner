"""Dependency management for MCPwner.

Clients and services for the registry-driven scan tools (SAST / SCA / Secrets /
Reconnaissance) are built generically from :data:`config.tools.TOOL_REGISTRY`
by :func:`get_client` / :func:`get_service`. CodeQL, Linguist and the workspace
layer have bespoke wiring and stay as explicit factories below.
"""

from functools import lru_cache
from typing import Any

from clients.base import BaseScanClient
from clients.codeql import CodeQLClient
from clients.linguist import LinguistClient
from config.config import load_config
from config.tools import TOOL_REGISTRY, ToolSpec
from repositories.workspace import WorkspaceRepository
from services.base_scan import BaseScanService
from services.codeql import CodeQLService
from services.linguist import LinguistService
from services.workspace import WorkspaceService


@lru_cache(maxsize=None)
def get_config():
    return load_config("config/config.yaml")


@lru_cache(maxsize=None)
def get_workspace_repository():
    return WorkspaceRepository()


def _resolve_service_url(spec: ToolSpec) -> str:
    """Resolve a tool's service URL from config, falling back to its default."""
    node: Any = get_config()
    for key in spec.config_path:
        node = node.get(key, {}) if isinstance(node, dict) else {}
    url = node.get("service_url") if isinstance(node, dict) else None
    return url or spec.default_url


@lru_cache(maxsize=None)
def get_client(name: str) -> BaseScanClient:
    spec = TOOL_REGISTRY[name]
    return BaseScanClient(_resolve_service_url(spec), name, spec.category)


@lru_cache(maxsize=None)
def get_service(name: str) -> BaseScanService:
    spec = TOOL_REGISTRY[name]
    return BaseScanService(get_workspace_repository(), get_client(name), spec.category)


@lru_cache(maxsize=None)
def get_workspace_service():
    return WorkspaceService(get_workspace_repository())


def _bespoke_service_url(section: str, default: str) -> str:
    """Resolve a non-registry tool's service URL from config, falling back to default."""
    node = get_config().get(section, {})
    url = node.get("service_url") if isinstance(node, dict) else None
    return url or default


@lru_cache(maxsize=None)
def get_linguist_client():
    return LinguistClient(_bespoke_service_url("linguist", "http://linguist:8081"))


@lru_cache(maxsize=None)
def get_linguist_service():
    return LinguistService(get_workspace_repository(), get_linguist_client())


@lru_cache(maxsize=None)
def get_codeql_client():
    return CodeQLClient(_bespoke_service_url("codeql", "http://codeql:8080"))


@lru_cache(maxsize=None)
def get_codeql_service():
    return CodeQLService(get_workspace_repository(), get_codeql_client(), get_linguist_service())
