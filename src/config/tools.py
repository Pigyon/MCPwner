"""Single source of truth for tool wiring (category, config path, default URL).

Every scan tool (SAST / SCA / Secrets / Reconnaissance) is described by exactly
one :class:`ToolSpec` entry here. ``deps.py`` builds its HTTP clients and
services from this registry, and the MCP scan/report tools derive their
``SUPPORTED_TOOLS`` lists from it, so a tool's name, category, config key and
default service URL live in one place instead of being restated across
``deps.py``, the per-category tool modules and the per-tool client/service
classes.

CodeQL and Linguist are intentionally NOT in this registry: they have bespoke
clients/services and extra constructor dependencies, so they stay wired
explicitly in ``deps.py``.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple


class ToolCategory(str, Enum):
    """Scan tool categories. ``str`` subclass so ``.value`` is usable as a plain
    string in config keys, report paths and dict lookups."""

    SAST = "sast"
    SCA = "sca"
    SECRETS = "secrets"
    RECONNAISSANCE = "reconnaissance"
    UTILITIES = "utilities"
    IAC = "iac"
    FUZZING = "fuzzing"
    DAST = "dast"
    POC = "poc"


@dataclass(frozen=True)
class ToolSpec:
    """Describes how to reach and classify a single scan tool."""

    name: str
    category: str
    config_path: Tuple[str, ...]
    default_url: str


def _spec(name: str, category: ToolCategory, config_path: Tuple[str, ...], default_url: str) -> ToolSpec:
    return ToolSpec(name=name, category=category.value, config_path=config_path, default_url=default_url)


# Order within each category is LLM-facing (drives SUPPORTED_TOOLS).
_SAST = ToolCategory.SAST
_SCA = ToolCategory.SCA
_SECRETS = ToolCategory.SECRETS
_RECON = ToolCategory.RECONNAISSANCE
_UTIL = ToolCategory.UTILITIES
_IAC = ToolCategory.IAC
_FUZZING = ToolCategory.FUZZING
_DAST = ToolCategory.DAST
_POC = ToolCategory.POC

_SPECS: Tuple[ToolSpec, ...] = (
    _spec("semgrep", _SAST, ("semgrep",), "http://semgrep:8082"),
    _spec("bandit", _SAST, ("bandit",), "http://bandit:8083"),
    _spec("gosec", _SAST, ("gosec",), "http://gosec:8084"),
    _spec("brakeman", _SAST, ("brakeman",), "http://brakeman:8085"),
    _spec("pmd", _SAST, ("pmd",), "http://pmd:8086"),
    _spec("psalm", _SAST, ("psalm",), "http://psalm:8087"),
    _spec("nodejsscan", _SAST, ("nodejsscan",), "http://nodejsscan:8088"),
    _spec("joern", _SAST, ("joern",), "http://joern:8089"),
    _spec("yasa", _SAST, ("yasa",), "http://yasa:8095"),
    _spec("opengrep", _SAST, ("opengrep",), "http://opengrep:8096"),
    _spec("osv-scanner", _SCA, ("osv_scanner",), "http://osv-scanner:8100"),
    _spec("grype", _SCA, ("grype",), "http://grype:8101"),
    _spec("retirejs", _SCA, ("retirejs",), "http://retirejs:8104"),
    _spec("syft", _SCA, ("syft",), "http://syft:8102"),
    _spec("gitleaks", _SECRETS, ("gitleaks",), "http://gitleaks:8090"),
    _spec("trufflehog", _SECRETS, ("trufflehog",), "http://trufflehog:8091"),
    _spec("whispers", _SECRETS, ("whispers",), "http://whispers:8092"),
    _spec("detect-secrets", _SECRETS, ("detect_secrets",), "http://detect-secrets:8093"),
    _spec("hawk-scanner", _SECRETS, ("hawk_scanner",), "http://hawk-scanner:8094"),
    _spec("subfinder", _RECON, ("reconnaissance", "subfinder"), "http://subfinder:8110"),
    _spec("amass", _RECON, ("reconnaissance", "amass"), "http://amass:8111"),
    _spec("httpx", _RECON, ("reconnaissance", "httpx"), "http://httpx:8112"),
    _spec("katana", _RECON, ("reconnaissance", "katana"), "http://katana:8113"),
    _spec("ffuf", _RECON, ("reconnaissance", "ffuf"), "http://ffuf:8114"),
    _spec("nmap", _RECON, ("reconnaissance", "nmap"), "http://nmap:8116"),
    _spec("masscan", _RECON, ("reconnaissance", "masscan"), "http://masscan:8117"),
    _spec("bbot", _RECON, ("reconnaissance", "bbot"), "http://bbot:8118"),
    _spec("arjun", _RECON, ("reconnaissance", "arjun"), "http://arjun:8119"),
    _spec("gau", _RECON, ("reconnaissance", "gau"), "http://gau:8115"),
    _spec("wafw00f", _RECON, ("reconnaissance", "wafw00f"), "http://wafw00f:8120"),
    _spec("kiterunner", _RECON, ("reconnaissance", "kiterunner"), "http://kiterunner:8121"),
    _spec("wiremock", _UTIL, ("utilities", "wiremock"), "http://wiremock:8130"),
    _spec("mitmproxy", _UTIL, ("utilities", "mitmproxy"), "http://mitmproxy:8131"),
    _spec("fuzzer", _UTIL, ("utilities", "fuzzer"), "http://fuzzer:8132"),
    _spec("chromium", _UTIL, ("utilities", "chromium"), "http://chromium:8133"),
    _spec("checkov", _IAC, ("iac", "checkov"), "http://checkov:8140"),
    _spec("kics", _IAC, ("iac", "kics"), "http://kics:8141"),
    _spec("terrascan", _IAC, ("iac", "terrascan"), "http://terrascan:8142"),
    _spec("tfsec", _IAC, ("iac", "tfsec"), "http://tfsec:8143"),
    _spec("hadolint", _IAC, ("iac", "hadolint"), "http://hadolint:8144"),
    _spec("atheris", _FUZZING, ("fuzzing", "atheris"), "http://atheris:8150"),
    _spec("jazzer", _FUZZING, ("fuzzing", "jazzer"), "http://jazzer:8151"),
    _spec("jazzerjs", _FUZZING, ("fuzzing", "jazzerjs"), "http://jazzerjs:8152"),
    _spec("php-fuzzer", _FUZZING, ("fuzzing", "php_fuzzer"), "http://php-fuzzer:8153"),
    _spec("sqlmap", _DAST, ("dast", "sqlmap"), "http://sqlmap:8160"),
    _spec("nosqlmap", _DAST, ("dast", "nosqlmap"), "http://nosqlmap:8161"),
    _spec("commix", _DAST, ("dast", "commix"), "http://commix:8162"),
    _spec("dalfox", _DAST, ("dast", "dalfox"), "http://dalfox:8163"),
    _spec("sstimap", _DAST, ("dast", "sstimap"), "http://sstimap:8164"),
    _spec("ssrfmap", _DAST, ("dast", "ssrfmap"), "http://ssrfmap:8165"),
    _spec("jwt_tool", _DAST, ("dast", "jwt_tool"), "http://jwt-tool:8166"),
    _spec("interactsh-client", _DAST, ("dast", "interactsh_client"), "http://interactsh-client:8167"),
    _spec("poc-sandbox", _POC, ("poc", "poc_sandbox"), "http://poc-sandbox:8134"),
)

TOOL_REGISTRY: Dict[str, ToolSpec] = {spec.name: spec for spec in _SPECS}


# User-facing aliases → canonical registry names. Lets callers use common
# alternative spellings without hitting an "unsupported tool" error (e.g. the
# Hawk-Eye / hawk_scanner secrets scanner is registered as "hawk-scanner").
TOOL_ALIASES: Dict[str, str] = {
    "hawkeye": "hawk-scanner",
    "hawk-eye": "hawk-scanner",
    "hawk_eye": "hawk-scanner",
    "hawk": "hawk-scanner",
    "detect_secrets": "detect-secrets",
    "osv": "osv-scanner",
    "osv_scanner": "osv-scanner",
    "jazzer.js": "jazzerjs",
    "jazzer-js": "jazzerjs",
    "jazzer_js": "jazzerjs",
    "php_fuzzer": "php-fuzzer",
    "phpfuzzer": "php-fuzzer",
    "php-fuzz": "php-fuzzer",
    "jwt-tool": "jwt_tool",
    "jwt": "jwt_tool",
    "interactsh": "interactsh-client",
    "interactsh_client": "interactsh-client",
}


def resolve_tool_name(name: str) -> str:
    """Map a user-supplied tool name to its canonical registry name.

    Falls back to the original name (so genuinely unknown tools still produce a
    clear "unsupported tool" error downstream)."""
    if not name:
        return name
    return TOOL_ALIASES.get(name.strip().lower(), name)


def tools_for_category(category: str) -> List[str]:
    """Return healthy tool names for a category, in registry (LLM-facing) order."""
    return [spec.name for spec in _SPECS if spec.category == category and spec.name in HEALTHY_TOOLS]


HEALTHY_TOOLS = set()


def filter_unhealthy_tools(healthy_names: set):
    """Update the healthy tools set."""
    global HEALTHY_TOOLS
    HEALTHY_TOOLS.clear()
    HEALTHY_TOOLS.update(healthy_names)


def get_bespoke_tools() -> List[str]:
    """Return healthy tools that have bespoke wiring and are not in the registry."""
    return [t for t in ["codeql", "linguist"] if t in HEALTHY_TOOLS]


CHAINABLE_TOOLS = ["httpx", "katana", "arjun", "gau", "wafw00f", "kiterunner", "ffuf"]
