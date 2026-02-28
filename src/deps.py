"""Dependency management for MCPwner.

Simple factory functions for service instantiation following MCP server conventions.
"""

from functools import lru_cache

from clients.codeql import CodeQLClient
from clients.linguist import LinguistClient
from clients.semgrep import SemgrepClient
from clients.bandit import BanditClient
from clients.gosec import GosecClient
from clients.brakeman import BrakemanClient
from clients.pmd import PMDClient
from clients.psalm import PsalmClient
from clients.secrets.gitleaks import GitleaksClient
from clients.secrets.trufflehog import TruffleHogClient

from config.config import load_config
from repositories.workspace import WorkspaceRepository

from services.codeql import CodeQLService
from services.linguist import LinguistService
from services.semgrep import SemgrepService
from services.bandit import BanditService
from services.gosec import GosecService
from services.brakeman import BrakemanService
from services.pmd import PMDService
from services.psalm import PsalmService
from services.secrets.gitleaks import GitleaksService
from services.secrets.trufflehog import TruffleHogService
from services.workspace import WorkspaceService


@lru_cache(maxsize=None)
def get_config():
    """Get configuration singleton."""
    return load_config("config/config.yaml")


@lru_cache(maxsize=None)
def get_workspace_repository():
    """Get workspace repository singleton."""
    return WorkspaceRepository()


@lru_cache(maxsize=None)
def get_codeql_client():
    """Get CodeQL client singleton."""
    config = get_config()
    return CodeQLClient(config["codeql"]["service_url"])


@lru_cache(maxsize=None)
def get_linguist_client():
    """Get Linguist client singleton."""
    config = get_config()
    return LinguistClient(config["linguist"]["service_url"])


@lru_cache(maxsize=None)
def get_workspace_service():
    """Get workspace service singleton."""
    return WorkspaceService(get_workspace_repository())


@lru_cache(maxsize=None)
def get_linguist_service():
    """Get Linguist service singleton."""
    return LinguistService(get_workspace_repository(), get_linguist_client())


@lru_cache(maxsize=None)
def get_codeql_service():
    """Get CodeQL service singleton."""
    return CodeQLService(
        get_workspace_repository(),
        get_codeql_client(),
        get_linguist_service()
    )


# SAST Clients and Services

@lru_cache(maxsize=None)
def get_semgrep_client():
    config = get_config()
    semgrep_url = config.get("semgrep", {}).get("service_url", "http://semgrep:8082")
    return SemgrepClient(semgrep_url)


@lru_cache(maxsize=None)
def get_semgrep_service():
    return SemgrepService(get_workspace_repository(), get_semgrep_client())


@lru_cache(maxsize=None)
def get_bandit_client():
    config = get_config()
    bandit_url = config.get("bandit", {}).get("service_url", "http://bandit:8083")
    return BanditClient(bandit_url)


@lru_cache(maxsize=None)
def get_bandit_service():
    return BanditService(get_workspace_repository(), get_bandit_client())


@lru_cache(maxsize=None)
def get_gosec_client():
    config = get_config()
    gosec_url = config.get("gosec", {}).get("service_url", "http://gosec:8084")
    return GosecClient(gosec_url)


@lru_cache(maxsize=None)
def get_gosec_service():
    return GosecService(get_workspace_repository(), get_gosec_client())


@lru_cache(maxsize=None)
def get_brakeman_client():
    config = get_config()
    brakeman_url = config.get("brakeman", {}).get("service_url", "http://brakeman:8085")
    return BrakemanClient(brakeman_url)


@lru_cache(maxsize=None)
def get_brakeman_service():
    return BrakemanService(get_workspace_repository(), get_brakeman_client())


@lru_cache(maxsize=None)
def get_pmd_client():
    config = get_config()
    pmd_url = config.get("pmd", {}).get("service_url", "http://pmd:8086")
    return PMDClient(pmd_url)


@lru_cache(maxsize=None)
def get_pmd_service():
    return PMDService(get_workspace_repository(), get_pmd_client())


@lru_cache(maxsize=None)
def get_psalm_client():
    config = get_config()
    psalm_url = config.get("psalm", {}).get("service_url", "http://psalm:8087")
    return PsalmClient(psalm_url)


@lru_cache(maxsize=None)
def get_psalm_service():
    return PsalmService(get_workspace_repository(), get_psalm_client())


@lru_cache(maxsize=None)
def get_gitleaks_client():
    config = get_config()
    gitleaks_url = config.get("gitleaks", {}).get("service_url", "http://gitleaks:8090")
    return GitleaksClient(gitleaks_url)


@lru_cache(maxsize=None)
def get_gitleaks_service():
    return GitleaksService(get_workspace_repository(), get_gitleaks_client())


@lru_cache(maxsize=None)
def get_trufflehog_client():
    config = get_config()
    trufflehog_url = config.get("trufflehog", {}).get("service_url", "http://trufflehog:8091")
    return TruffleHogClient(trufflehog_url)


@lru_cache(maxsize=None)
def get_trufflehog_service():
    return TruffleHogService(get_workspace_repository(), get_trufflehog_client())


def reset_dependencies():
    """Reset all dependencies (useful for testing)."""
    get_config.cache_clear()
    get_workspace_repository.cache_clear()
    get_codeql_client.cache_clear()
    get_linguist_client.cache_clear()
    get_workspace_service.cache_clear()
    get_linguist_service.cache_clear()
    get_codeql_service.cache_clear()
    
    get_semgrep_client.cache_clear()
    get_semgrep_service.cache_clear()
    get_bandit_client.cache_clear()
    get_bandit_service.cache_clear()
    get_gosec_client.cache_clear()
    get_gosec_service.cache_clear()
    get_brakeman_client.cache_clear()
    get_brakeman_service.cache_clear()
    get_pmd_client.cache_clear()
    get_pmd_service.cache_clear()
    get_psalm_client.cache_clear()
    get_psalm_service.cache_clear()
    get_gitleaks_client.cache_clear()
    get_gitleaks_service.cache_clear()
    get_trufflehog_client.cache_clear()
    get_trufflehog_service.cache_clear()
