"""Dependency management for MCPwner.

Simple factory functions for service instantiation following MCP server conventions.
"""

from config.config import load_config
from repositories.workspace import WorkspaceRepository
from clients.codeql import CodeQLClient
from clients.linguist import LinguistClient
from services.workspace import WorkspaceService
from services.codeql import CodeQLService
from services.linguist import LinguistService
from services.context import ContextService

# Global instances
_config = None
_workspace_repository = None
_codeql_client = None
_linguist_client = None
_workspace_service = None
_codeql_service = None
_linguist_service = None
_context_service = None


def get_config():
    """Get configuration singleton."""
    global _config
    if _config is None:
        _config = load_config("config/config.yaml")
    return _config


def get_workspace_repository():
    """Get workspace repository singleton."""
    global _workspace_repository
    if _workspace_repository is None:
        _workspace_repository = WorkspaceRepository()
    return _workspace_repository


def get_codeql_client():
    """Get CodeQL client singleton."""
    global _codeql_client
    if _codeql_client is None:
        config = get_config()
        _codeql_client = CodeQLClient(config["codeql"]["service_url"])
    return _codeql_client


def get_linguist_client():
    """Get Linguist client singleton."""
    global _linguist_client
    if _linguist_client is None:
        config = get_config()
        _linguist_client = LinguistClient(config["linguist"]["service_url"])
    return _linguist_client


def get_workspace_service():
    """Get workspace service singleton."""
    global _workspace_service
    if _workspace_service is None:
        _workspace_service = WorkspaceService(get_workspace_repository())
    return _workspace_service


def get_codeql_service():
    """Get CodeQL service singleton."""
    global _codeql_service
    if _codeql_service is None:
        _codeql_service = CodeQLService(
            get_workspace_repository(),
            get_codeql_client()
        )
    return _codeql_service


def get_linguist_service():
    """Get Linguist service singleton."""
    global _linguist_service
    if _linguist_service is None:
        _linguist_service = LinguistService(
            get_workspace_repository(),
            get_linguist_client()
        )
    return _linguist_service


def get_context_service():
    """Get context service singleton."""
    global _context_service
    if _context_service is None:
        _context_service = ContextService(
            get_workspace_repository(),
            codeql_bin="codeql"
        )
    return _context_service


def reset_dependencies():
    """Reset all dependencies (useful for testing)."""
    global _config, _workspace_repository, _codeql_client, _linguist_client
    global _workspace_service, _codeql_service, _linguist_service, _context_service
    
    _config = None
    _workspace_repository = None
    _codeql_client = None
    _linguist_client = None
    _workspace_service = None
    _codeql_service = None
    _linguist_service = None
    _context_service = None
