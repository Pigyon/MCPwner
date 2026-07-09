"""Reconnaissance tool discovery MCP tool."""

from typing import Optional

from api.tools.common import filter_tools_by_language, handle_tool_error

RECONNAISSANCE_TOOLS = {
    "subfinder": {
        "name": "Subfinder",
        "description": "Subdomain discovery tool. Accepts 'target' (domain) or 'domain' in config.",
    },
    "amass": {
        "name": "Amass",
        "description": (
            "Network mapping and attack surface discovery. "
            "Config: target/domain (required), passive (bool), timeout (minutes, default: 30)."
        ),
    },
    "httpx": {
        "name": "httpx",
        "description": (
            "HTTP toolkit for probing and analysis of web servers. "
            "Supports chaining: pass source_tool='subfinder' (or amass, bbot, nmap, masscan, ffuf) "
            "to auto-read targets from a previous scan's report. "
            "Also accepts 'targets' list for batch probing or single 'target'."
        ),
    },
    "katana": {
        "name": "Katana",
        "description": (
            "Web crawling framework for spidering and URL extraction. "
            "Supports chaining: pass source_tool='httpx' "
            "(or subfinder, amass, bbot, nmap, masscan, ffuf, gau) "
            "to auto-read targets from a previous scan's report. "
            "Also accepts 'targets' list for batch crawling or single 'target'. "
            "Optional: depth, js_crawl, headless, scope."
        ),
    },
    "ffuf": {
        "name": "ffuf",
        "description": (
            "Fast web fuzzer for content discovery. "
            "Supports chaining: pass source_tool='httpx' (or katana, gau) "
            "to auto-extract a base URL from a previous scan's report. "
            "Requires 'url' or 'target' with FUZZ keyword (auto-appended if missing). "
            "Optional: wordlist, extensions, match_codes, filter_codes, threads, rate."
        ),
    },
    "nmap": {
        "name": "Nmap",
        "description": (
            "Network scanner for host and service discovery. "
            "Config: target (required), ports (default: '1-1000'), timeout (seconds, default: 300)."
        ),
    },
    "masscan": {
        "name": "Masscan",
        "description": (
            "Fast port scanner for large-scale scanning. "
            "Config: target (required, IP or hostname), ports (default: '1-1000'), "
            "rate (packets/sec, default: 100)."
        ),
    },
    "arjun": {
        "name": "Arjun",
        "description": (
            "HTTP parameter discovery tool for finding hidden query and body parameters. "
            "Supports chaining: pass source_tool='httpx' (or katana, gau, ffuf, bbot) "
            "to auto-read URLs from a previous scan's report. "
            "Also accepts 'targets' list for batch testing or single 'target'. "
            "Optional: method (GET/POST/JSON), headers, threads, wordlist."
        ),
    },
    "bbot": {
        "name": "bbot",
        "description": (
            "OSINT automation framework with 90+ modules. Use run_reconnaissance_scan with tool='bbot'. "
            "The scan returns a structured summary with subdomains, IPs, open ports, URLs, "
            "technologies, vulnerabilities, and suggested_next_steps for chaining.\n\n"
            "PRESETS (via config.preset, comma-separated for multiple):\n"
            "  subdomain-enum (default) – 51 modules: DNS, certs, Shodan, APIs\n"
            "  web-basic – 18 modules: HTTP probe, git, robots, GraphQL\n"
            "  web-thorough – 32 modules: SSRF, smuggling, 403 bypass, lightfuzz\n"
            "  nuclei / nuclei-intense – vulnerability scanning\n"
            "  cloud-enum – S3/GCS/Azure bucket discovery\n"
            "  email-enum – email harvesting\n"
            "  spider – recursive web crawl\n"
            "  paramminer – parameter brute-force\n"
            "  deep – stacks 8 presets + aggressive (very slow)\n\n"
            "WORKFLOW: subdomain-enum first → web-thorough on findings → nuclei for vulns"
        ),
    },
    "gau": {
        "name": "gau",
        "description": (
            "Get All URLs from web archives (Wayback Machine, Common Crawl, OTX, URLScan). "
            "Supports chaining: pass source_tool='subfinder' (or amass, bbot, httpx) "
            "to auto-read domains from a previous scan's report. "
            "Also accepts 'targets' list for batch querying or single 'target'. "
            "Optional: providers, blacklist, threads, from, to."
        ),
    },
    "wafw00f": {
        "name": "wafw00f",
        "description": (
            "Web Application Firewall detection and fingerprinting tool. "
            "Supports chaining: pass source_tool='httpx' (or subfinder, amass, bbot, katana) "
            "to auto-read targets from a previous scan's report. "
            "Also accepts 'targets' list for batch testing or single 'target'. "
            "Optional: test_all (test all WAF signatures), verbose."
        ),
    },
    "kiterunner": {
        "name": "Kiterunner",
        "description": (
            "Context-aware content discovery tool by Assetnote using API-aware wordlists. "
            "Supports chaining: pass source_tool='httpx' (or katana, gau, subfinder, amass, bbot) "
            "to auto-read targets from a previous scan's report. "
            "Also accepts 'targets' list for batch scanning or single 'target'. "
            "Optional: wordlist, threads, max_connection_per_host."
        ),
    },
}


@handle_tool_error
def reconnaissance_list_tools(workspace_id: Optional[str] = None, show_all: bool = False) -> dict:
    """
    List available Reconnaissance tools.

    Args:
        workspace_id: Optional workspace ID (reserved for future filtering)
        show_all: If True, show all tools (default behavior for reconnaissance tools)

    Returns:
        Dictionary with available tools and their metadata
    """
    return filter_tools_by_language("reconnaissance", RECONNAISSANCE_TOOLS, workspace_id, show_all)
