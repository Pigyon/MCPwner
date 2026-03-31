"""Dependency management for MCPwner.

Simple factory functions for service instantiation following MCP server conventions.
"""

from functools import lru_cache

from clients.bandit import BanditClient
from clients.brakeman import BrakemanClient
from clients.codeql import CodeQLClient
from clients.gosec import GosecClient
from clients.joern import JoernClient
from clients.linguist import LinguistClient
from clients.nodejsscan import NodeJsScanClient
from clients.opengrep import OpengrepClient
from clients.pmd import PMDClient
from clients.psalm import PsalmClient
from clients.reconnaissance.amass import AmassClient
from clients.reconnaissance.arjun import ArjunClient
from clients.reconnaissance.bbot import BbotClient
from clients.reconnaissance.ffuf import FfufClient
from clients.reconnaissance.gau import GauClient
from clients.reconnaissance.httpx import HttpxClient
from clients.reconnaissance.katana import KatanaClient
from clients.reconnaissance.kiterunner import KiterunnerClient
from clients.reconnaissance.masscan import MasscanClient
from clients.reconnaissance.nmap import NmapClient
from clients.reconnaissance.subfinder import SubfinderClient
from clients.reconnaissance.wafw00f import Wafw00fClient
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
from clients.yasa import YASAClient
from config.config import load_config
from repositories.workspace import WorkspaceRepository
from services.bandit import BanditService
from services.brakeman import BrakemanService
from services.codeql import CodeQLService
from services.gosec import GosecService
from services.joern import JoernService
from services.linguist import LinguistService
from services.nodejsscan import NodeJsScanService
from services.opengrep import OpengrepService
from services.pmd import PMDService
from services.psalm import PsalmService
from services.reconnaissance.amass import AmassService
from services.reconnaissance.arjun import ArjunService
from services.reconnaissance.bbot import BbotService
from services.reconnaissance.ffuf import FfufService
from services.reconnaissance.gau import GauService
from services.reconnaissance.httpx import HttpxService
from services.reconnaissance.katana import KatanaService
from services.reconnaissance.kiterunner import KiterunnerService
from services.reconnaissance.masscan import MasscanService
from services.reconnaissance.nmap import NmapService
from services.reconnaissance.subfinder import SubfinderService
from services.reconnaissance.wafw00f import Wafw00fService
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
from services.yasa import YASAService


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


@lru_cache(maxsize=None)
def get_nodejsscan_client():
    config = get_config()
    nodejsscan_url = config.get("nodejsscan", {}).get("service_url", "http://nodejsscan:8088")
    return NodeJsScanClient(nodejsscan_url)


@lru_cache(maxsize=None)
def get_nodejsscan_service():
    return NodeJsScanService(get_workspace_repository(), get_nodejsscan_client())


@lru_cache(maxsize=None)
def get_joern_client():
    config = get_config()
    joern_url = config.get("joern", {}).get("service_url", "http://joern:8089")
    return JoernClient(joern_url)


@lru_cache(maxsize=None)
def get_joern_service():
    return JoernService(get_workspace_repository(), get_joern_client())


@lru_cache(maxsize=None)
def get_yasa_client():
    config = get_config()
    yasa_url = config.get("yasa", {}).get("service_url", "http://yasa:8095")
    return YASAClient(yasa_url)


@lru_cache(maxsize=None)
def get_yasa_service():
    return YASAService(get_workspace_repository(), get_yasa_client())


@lru_cache(maxsize=None)
def get_opengrep_client():
    config = get_config()
    opengrep_url = config.get("opengrep", {}).get("service_url", "http://opengrep:8096")
    return OpengrepClient(opengrep_url)


@lru_cache(maxsize=None)
def get_opengrep_service():
    return OpengrepService(get_workspace_repository(), get_opengrep_client())


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


@lru_cache(maxsize=None)
def get_bbot_client():
    config = get_config()
    bbot_url = config.get("reconnaissance", {}).get("bbot", {}).get("service_url", "http://bbot:8118")
    return BbotClient(bbot_url)


@lru_cache(maxsize=None)
def get_bbot_service():
    return BbotService(get_workspace_repository(), get_bbot_client())


@lru_cache(maxsize=None)
def get_httpx_client():
    config = get_config()
    httpx_url = config.get("reconnaissance", {}).get("httpx", {}).get("service_url", "http://httpx:8112")
    return HttpxClient(httpx_url)


@lru_cache(maxsize=None)
def get_httpx_service():
    return HttpxService(get_workspace_repository(), get_httpx_client())


@lru_cache(maxsize=None)
def get_katana_client():
    config = get_config()
    katana_url = (
        config.get("reconnaissance", {}).get("katana", {}).get("service_url", "http://katana:8113")
    )
    return KatanaClient(katana_url)


@lru_cache(maxsize=None)
def get_katana_service():
    return KatanaService(get_workspace_repository(), get_katana_client())


@lru_cache(maxsize=None)
def get_gau_client():
    config = get_config()
    gau_url = config.get("reconnaissance", {}).get("gau", {}).get("service_url", "http://gau:8115")
    return GauClient(gau_url)


@lru_cache(maxsize=None)
def get_gau_service():
    return GauService(get_workspace_repository(), get_gau_client())


@lru_cache(maxsize=None)
def get_arjun_client():
    config = get_config()
    arjun_url = config.get("reconnaissance", {}).get("arjun", {}).get("service_url", "http://arjun:8119")
    return ArjunClient(arjun_url)


@lru_cache(maxsize=None)
def get_arjun_service():
    return ArjunService(get_workspace_repository(), get_arjun_client())


@lru_cache(maxsize=None)
def get_wafw00f_client():
    config = get_config()
    wafw00f_url = (
        config.get("reconnaissance", {}).get("wafw00f", {}).get("service_url", "http://wafw00f:8120")
    )
    return Wafw00fClient(wafw00f_url)


@lru_cache(maxsize=None)
def get_wafw00f_service():
    return Wafw00fService(get_workspace_repository(), get_wafw00f_client())


@lru_cache(maxsize=None)
def get_kiterunner_client():
    config = get_config()
    kiterunner_url = (
        config.get("reconnaissance", {})
        .get("kiterunner", {})
        .get("service_url", "http://kiterunner:8121")
    )
    return KiterunnerClient(kiterunner_url)


@lru_cache(maxsize=None)
def get_kiterunner_service():
    return KiterunnerService(get_workspace_repository(), get_kiterunner_client())
