"""Dependency management for MCPwner.

Simple factory functions for service instantiation following MCP server conventions.
"""

from clients.codeql import CodeQLClient
from clients.linguist import LinguistClient
from clients.semgrep import SemgrepClient
from config.config import load_config
from repositories.workspace import WorkspaceRepository
from services.codeql import CodeQLService
from services.context import ContextService
from services.linguist import LinguistService
from services.semgrep import SemgrepService
from services.workspace import WorkspaceService

# Global instances
_config = None
_workspace_repository = None
_codeql_client = None
_linguist_client = None
_workspace_service = None
_codeql_service = None
_linguist_service = None
_context_service = None

# SAST tool instances
_semgrep_client = None
_semgrep_service = None
_bandit_client = None
_bandit_service = None
_gosec_client = None
_gosec_service = None
_brakeman_client = None
_brakeman_service = None
_pmd_client = None
_pmd_service = None
_psalm_client = None
_psalm_service = None


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
        _codeql_service = CodeQLService(get_workspace_repository(), get_codeql_client())
    return _codeql_service


def get_linguist_service():
    """Get Linguist service singleton."""
    global _linguist_service
    if _linguist_service is None:
        _linguist_service = LinguistService(get_workspace_repository(), get_linguist_client())
    return _linguist_service


def get_context_service():
    """Get context service singleton."""
    global _context_service
    if _context_service is None:
        _context_service = ContextService(get_workspace_repository(), codeql_bin="codeql")
    return _context_service


# SAST Service Getters


def get_semgrep_service():
    """Get Semgrep service singleton."""
    global _semgrep_service, _semgrep_client
    if _semgrep_service is None:
        if _semgrep_client is None:
            config = get_config()
            semgrep_url = config.get("semgrep", {}).get("service_url", "http://semgrep:8082")
            _semgrep_client = SemgrepClient(semgrep_url)

        _semgrep_service = SemgrepService(get_workspace_repository(), _semgrep_client)
    return _semgrep_service


def get_bandit_service():
    """Get Bandit service singleton."""
    global _bandit_service, _bandit_client
    if _bandit_service is None:
        if _bandit_client is None:
            config = get_config()
            bandit_url = config.get("bandit", {}).get("service_url", "http://bandit:8083")
            from clients.bandit import BanditClient

            _bandit_client = BanditClient(bandit_url)

        from services.bandit import BanditService

        _bandit_service = BanditService(get_workspace_repository(), _bandit_client)
    return _bandit_service


def get_gosec_service():
    """Get Gosec service singleton."""
    global _gosec_service, _gosec_client
    if _gosec_service is None:
        if _gosec_client is None:
            config = get_config()
            gosec_url = config.get("gosec", {}).get("service_url", "http://gosec:8084")
            from clients.gosec import GosecClient

            _gosec_client = GosecClient(gosec_url)

        from services.gosec import GosecService

        _gosec_service = GosecService(get_workspace_repository(), _gosec_client)
    return _gosec_service


def get_brakeman_service():
    """Get Brakeman service singleton."""
    global _brakeman_service, _brakeman_client
    if _brakeman_service is None:
        if _brakeman_client is None:
            config = get_config()
            brakeman_url = config.get("brakeman", {}).get("service_url", "http://brakeman:8085")
            from clients.brakeman import BrakemanClient

            _brakeman_client = BrakemanClient(brakeman_url)

        from services.brakeman import BrakemanService

        _brakeman_service = BrakemanService(get_workspace_repository(), _brakeman_client)
    return _brakeman_service


def get_pmd_service():
    """Get PMD service singleton."""
    global _pmd_service
    if _pmd_service is None:
        # TODO: Implement PMDService and PMDClient
        # from services.pmd import PMDService
        # from clients.pmd import PMDClient
        # config = get_config()
        # _pmd_service = PMDService(
        #     get_workspace_repository(),
        #     PMDClient(config.get("pmd", {}).get("service_url", "http://pmd:8086"))
        # )
        raise NotImplementedError("PMD service not yet implemented")
    return _pmd_service


def get_psalm_service():
    """Get Psalm service singleton."""
    global _psalm_service
    if _psalm_service is None:
        # TODO: Implement PsalmService and PsalmClient
        # from services.psalm import PsalmService
        # from clients.psalm import PsalmClient
        # config = get_config()
        # _psalm_service = PsalmService(
        #     get_workspace_repository(),
        #     PsalmClient(config.get("psalm", {}).get("service_url", "http://psalm:8087"))
        # )
        raise NotImplementedError("Psalm service not yet implemented")
    return _psalm_service


def reset_dependencies():
    """Reset all dependencies (useful for testing)."""
    global _config, _workspace_repository, _codeql_client, _linguist_client
    global _workspace_service, _codeql_service, _linguist_service, _context_service
    global _semgrep_client, _semgrep_service, _bandit_client, _bandit_service
    global _gosec_client, _gosec_service, _brakeman_client, _brakeman_service
    global _pmd_client, _pmd_service, _psalm_client, _psalm_service

    _config = None
    _workspace_repository = None
    _codeql_client = None
    _linguist_client = None
    _workspace_service = None
    _codeql_service = None
    _linguist_service = None
    _context_service = None

    # Reset SAST tool instances
    _semgrep_client = None
    _semgrep_service = None
    _bandit_client = None
    _bandit_service = None
    _gosec_client = None
    _gosec_service = None
    _brakeman_client = None
    _brakeman_service = None
    _pmd_client = None
    _pmd_service = None
    _psalm_client = None
    _psalm_service = None
