"""Dependency management for MCPwner.

Simple factory functions for service instantiation following MCP server conventions.
"""

from functools import lru_cache

from clients.bandit import BanditClient
from clients.brakeman import BrakemanClient
from clients.codeql import CodeQLClient
from clients.gosec import GosecClient
from clients.linguist import LinguistClient
from clients.pmd import PMDClient
from clients.psalm import PsalmClient
from clients.reconnaissance.amass import AmassClient
from clients.reconnaissance.ffuf import FfufClient
from clients.reconnaissance.masscan import MasscanClient
from clients.reconnaissance.nmap import NmapClient
from clients.reconnaissance.subfinder import SubfinderClient
from clients.sca.grype import GrypeClient
from clients.sca.osv_scanner import OSVScannerClient
from clients.sca.retirejs import RetireJSClient
from clients.sca.syft import SyftClient
from clients.secrets.detect_secrets import DetectSecretsClient
from clients.secrets.gitleaks import GitleaksClient
from clients.secrets.hawk_scanner import HawkScannerClient
from clients.secrets.trufflehog import TruffleHogClient
from clients.secrets.whispers import WhispersClient
from clients.semgrep import SemgrepClient
from config.config import load_config
from repositories.workspace import WorkspaceRepository
from services.bandit import BanditService
from services.brakeman import BrakemanService
from services.codeql import CodeQLService
from services.gosec import GosecService
from services.linguist import LinguistService
from services.pmd import PMDService
from services.psalm import PsalmService
from services.reconnaissance.amass import AmassService
from services.reconnaissance.ffuf import FfufService
from services.reconnaissance.masscan import MasscanService
from services.reconnaissance.nmap import NmapService
from services.reconnaissance.subfinder import SubfinderService
from services.sca.grype import GrypeService
from services.sca.osv_scanner import OSVScannerService
from services.sca.retirejs import RetireJSService
from services.sca.syft import SyftService
from services.secrets.detect_secrets import DetectSecretsService
from services.secrets.gitleaks import GitleaksService
from services.secrets.hawk_scanner import HawkScannerService
from services.secrets.trufflehog import TruffleHogService
from services.secrets.whispers import WhispersService
from services.semgrep import SemgrepService
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
    return CodeQLService(get_workspace_repository(), get_codeql_client(), get_linguist_service())


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


# SCA Clients and Services


@lru_cache(maxsize=None)
def get_osv_scanner_client():
    config = get_config()
    osv_scanner_url = config.get("osv_scanner", {}).get("service_url", "http://osv-scanner:8100")
    return OSVScannerClient(osv_scanner_url)


@lru_cache(maxsize=None)
def get_osv_scanner_service():
    return OSVScannerService(get_workspace_repository(), get_osv_scanner_client())


@lru_cache(maxsize=None)
def get_grype_client():
    config = get_config()
    grype_url = config.get("grype", {}).get("service_url", "http://grype:8101")
    return GrypeClient(grype_url)


@lru_cache(maxsize=None)
def get_grype_service():
    return GrypeService(get_workspace_repository(), get_grype_client())


@lru_cache(maxsize=None)
def get_syft_client():
    config = get_config()
    syft_url = config.get("syft", {}).get("service_url", "http://syft:8102")
    return SyftClient(syft_url)


@lru_cache(maxsize=None)
def get_syft_service():
    return SyftService(get_workspace_repository(), get_syft_client())


@lru_cache(maxsize=None)
def get_retirejs_client():
    config = get_config()
    retirejs_url = config.get("retirejs", {}).get("service_url", "http://retirejs:8104")
    return RetireJSClient(retirejs_url)


@lru_cache(maxsize=None)
def get_retirejs_service():
    return RetireJSService(get_workspace_repository(), get_retirejs_client())


# Secrets Clients and Services


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


@lru_cache(maxsize=None)
def get_detect_secrets_client():
    config = get_config()
    detect_secrets_url = config.get("detect_secrets", {}).get(
        "service_url", "http://detect-secrets:8092"
    )
    return DetectSecretsClient(detect_secrets_url)


@lru_cache(maxsize=None)
def get_detect_secrets_service():
    return DetectSecretsService(get_workspace_repository(), get_detect_secrets_client())


@lru_cache(maxsize=None)
def get_whispers_client():
    config = get_config()
    whispers_url = config.get("whispers", {}).get("service_url", "http://whispers:8093")
    return WhispersClient(whispers_url)


@lru_cache(maxsize=None)
def get_whispers_service():
    return WhispersService(get_workspace_repository(), get_whispers_client())


@lru_cache(maxsize=None)
def get_hawk_scanner_client():
    config = get_config()
    hawk_scanner_url = config.get("hawk_scanner", {}).get("service_url", "http://hawk-scanner:8094")
    return HawkScannerClient(hawk_scanner_url)


@lru_cache(maxsize=None)
def get_hawk_scanner_service():
    return HawkScannerService(get_workspace_repository(), get_hawk_scanner_client())


# Reconnaissance Clients and Services


@lru_cache(maxsize=None)
def get_subfinder_client():
    config = get_config()
    subfinder_url = (
        config.get("reconnaissance", {}).get("subfinder", {}).get("service_url", "http://subfinder:8110")
    )
    return SubfinderClient(subfinder_url)


@lru_cache(maxsize=None)
def get_subfinder_service():
    return SubfinderService(get_workspace_repository(), get_subfinder_client())


@lru_cache(maxsize=None)
def get_amass_client():
    config = get_config()
    amass_url = config.get("reconnaissance", {}).get("amass", {}).get("service_url", "http://amass:8111")
    return AmassClient(amass_url)


@lru_cache(maxsize=None)
def get_amass_service():
    return AmassService(get_workspace_repository(), get_amass_client())


@lru_cache(maxsize=None)
def get_masscan_client():
    config = get_config()
    masscan_url = (
        config.get("reconnaissance", {}).get("masscan", {}).get("service_url", "http://masscan:8117")
    )
    return MasscanClient(masscan_url)


@lru_cache(maxsize=None)
def get_masscan_service():
    return MasscanService(get_workspace_repository(), get_masscan_client())


@lru_cache(maxsize=None)
def get_nmap_client():
    config = get_config()
    nmap_url = config.get("reconnaissance", {}).get("nmap", {}).get("service_url", "http://nmap:8116")
    return NmapClient(nmap_url)


@lru_cache(maxsize=None)
def get_nmap_service():
    return NmapService(get_workspace_repository(), get_nmap_client())


@lru_cache(maxsize=None)
def get_ffuf_client():
    config = get_config()
    ffuf_url = config.get("reconnaissance", {}).get("ffuf", {}).get("service_url", "http://ffuf:8114")
    return FfufClient(ffuf_url)


@lru_cache(maxsize=None)
def get_ffuf_service():
    return FfufService(get_workspace_repository(), get_ffuf_client())
