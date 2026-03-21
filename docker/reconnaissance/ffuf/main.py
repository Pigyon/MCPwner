"""
ffuf Service - Fast Web Fuzzer

Available wordlists:
- /usr/share/wordlists/common.txt - Common files and directories
- /usr/share/wordlists/parameters.txt - Common HTTP parameters
- /usr/share/wordlists/subdomains.txt - Common subdomain names
"""

import logging
from pathlib import Path
from typing import List

from common.base_service import create_scanner_app
from common.models import ScanRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "ffuf"
VERSION_CMD = ["ffuf", "-V"]

# Available wordlists
WORDLISTS = {
    "common": "/usr/share/wordlists/common.txt",
    "parameters": "/usr/share/wordlists/parameters.txt",
    "subdomains": "/usr/share/wordlists/subdomains.txt",
}


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build ffuf scan command.

    Config options:
    - url/target: Target URL with FUZZ keyword (required)
    - wordlist: Path to wordlist or name (common/parameters/subdomains)
    - extensions: Comma-separated file extensions (e.g., "php,html,js")
    - match_codes: HTTP status codes to match (e.g., "200,301")
    - filter_codes: HTTP status codes to filter out (e.g., "404")
    - match_size: Response size to match
    - filter_size: Response size to filter out
    - threads: Number of threads (default: 40)
    - rate: Requests per second limit
    - timeout: Request timeout in seconds
    - silent: Silent mode (boolean)
    """
    # Get URL from config (accept both 'url' and 'target' for compatibility)
    url = ""
    if request.config:
        url = request.config.get("url") or request.config.get("target", "")

    if not url:
        raise ValueError("URL is required in config for ffuf scan (use 'url' or 'target' field)")

    # Auto-add FUZZ keyword if missing
    if "FUZZ" not in url:
        # Smart FUZZ placement based on URL structure
        if url.endswith("/"):
            url = url + "FUZZ"
            logger.info(f"Auto-added FUZZ keyword to URL: {url}")
        else:
            url = url + "/FUZZ"
            logger.info(f"Auto-added /FUZZ to URL: {url}")

    # Get wordlist from config - support both path and name
    wordlist = "/usr/share/wordlists/common.txt"
    if request.config and "wordlist" in request.config:
        wordlist_input = request.config["wordlist"]
        # Check if it's a named wordlist, otherwise use as path
        wordlist = WORDLISTS.get(wordlist_input, wordlist_input)

    logger.info(f"Using wordlist: {wordlist}")

    # ffuf command with JSON output
    # FUZZ keyword in URL will be replaced with wordlist entries
    cmd = ["ffuf", "-u", url, "-w", wordlist, "-o", str(output_path), "-of", "json"]

    # Add optional parameters if provided
    if request.config:
        # Extensions (e.g., "php,html,js")
        if "extensions" in request.config:
            cmd.extend(["-e", request.config["extensions"]])

        # Match HTTP status codes (default: 200,204,301,302,307,401,403,405)
        if "match_codes" in request.config:
            cmd.extend(["-mc", request.config["match_codes"]])

        # Filter HTTP status codes
        if "filter_codes" in request.config:
            cmd.extend(["-fc", request.config["filter_codes"]])

        # Match response size
        if "match_size" in request.config:
            cmd.extend(["-ms", str(request.config["match_size"])])

        # Filter response size
        if "filter_size" in request.config:
            cmd.extend(["-fs", str(request.config["filter_size"])])

        # Threads (default: 40)
        if "threads" in request.config:
            cmd.extend(["-t", str(request.config["threads"])])

        # Rate limit (requests per second)
        if "rate" in request.config:
            cmd.extend(["-rate", str(request.config["rate"])])

        # Timeout (seconds)
        if "timeout" in request.config:
            cmd.extend(["-timeout", str(request.config["timeout"])])

        # Silent mode
        if request.config.get("silent", False):
            cmd.append("-s")

    return cmd


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json",
    tool_category="reconnaissance",
)
