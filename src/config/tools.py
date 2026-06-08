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
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class ToolSpec:
    """Describes how to reach and classify a single scan tool."""

    name: str
    category: str  # "sast" | "sca" | "secrets" | "reconnaissance"
    config_path: Tuple[str, ...]  # keys to walk in config.yaml to find service_url
    default_url: str


def _spec(name: str, category: str, config_path: Tuple[str, ...], default_url: str) -> ToolSpec:
    return ToolSpec(name=name, category=category, config_path=config_path, default_url=default_url)


# Order within each category is LLM-facing (it drives SUPPORTED_TOOLS), so it is
# preserved here. Dict insertion order is guaranteed in Python 3.7+.
_SPECS: Tuple[ToolSpec, ...] = (
    # --- SAST ---
    _spec("semgrep", "sast", ("semgrep",), "http://semgrep:8082"),
    _spec("bandit", "sast", ("bandit",), "http://bandit:8083"),
    _spec("gosec", "sast", ("gosec",), "http://gosec:8084"),
    _spec("brakeman", "sast", ("brakeman",), "http://brakeman:8085"),
    _spec("pmd", "sast", ("pmd",), "http://pmd:8086"),
    _spec("psalm", "sast", ("psalm",), "http://psalm:8087"),
    _spec("nodejsscan", "sast", ("nodejsscan",), "http://nodejsscan:8088"),
    _spec("joern", "sast", ("joern",), "http://joern:8089"),
    _spec("yasa", "sast", ("yasa",), "http://yasa:8095"),
    _spec("opengrep", "sast", ("opengrep",), "http://opengrep:8096"),
    # --- SCA ---
    _spec("osv-scanner", "sca", ("osv_scanner",), "http://osv-scanner:8100"),
    _spec("grype", "sca", ("grype",), "http://grype:8101"),
    _spec("retirejs", "sca", ("retirejs",), "http://retirejs:8104"),
    _spec("syft", "sca", ("syft",), "http://syft:8102"),
    # --- Secrets ---
    _spec("gitleaks", "secrets", ("gitleaks",), "http://gitleaks:8090"),
    _spec("trufflehog", "secrets", ("trufflehog",), "http://trufflehog:8091"),
    _spec("whispers", "secrets", ("whispers",), "http://whispers:8092"),
    _spec("detect-secrets", "secrets", ("detect_secrets",), "http://detect-secrets:8093"),
    _spec("hawk-scanner", "secrets", ("hawk_scanner",), "http://hawk-scanner:8094"),
    # --- Reconnaissance ---
    _spec("subfinder", "reconnaissance", ("reconnaissance", "subfinder"), "http://subfinder:8110"),
    _spec("amass", "reconnaissance", ("reconnaissance", "amass"), "http://amass:8111"),
    _spec("httpx", "reconnaissance", ("reconnaissance", "httpx"), "http://httpx:8112"),
    _spec("katana", "reconnaissance", ("reconnaissance", "katana"), "http://katana:8113"),
    _spec("ffuf", "reconnaissance", ("reconnaissance", "ffuf"), "http://ffuf:8114"),
    _spec("nmap", "reconnaissance", ("reconnaissance", "nmap"), "http://nmap:8116"),
    _spec("masscan", "reconnaissance", ("reconnaissance", "masscan"), "http://masscan:8117"),
    _spec("bbot", "reconnaissance", ("reconnaissance", "bbot"), "http://bbot:8118"),
    _spec("arjun", "reconnaissance", ("reconnaissance", "arjun"), "http://arjun:8119"),
    _spec("gau", "reconnaissance", ("reconnaissance", "gau"), "http://gau:8115"),
    _spec("wafw00f", "reconnaissance", ("reconnaissance", "wafw00f"), "http://wafw00f:8120"),
    _spec("kiterunner", "reconnaissance", ("reconnaissance", "kiterunner"), "http://kiterunner:8121"),
)

TOOL_REGISTRY: Dict[str, ToolSpec] = {spec.name: spec for spec in _SPECS}


def tools_for_category(category: str) -> List[str]:
    """Return tool names for a category, in registry (LLM-facing) order."""
    return [spec.name for spec in _SPECS if spec.category == category]
