"""
Amass Service - Network Mapping and Attack Surface Discovery Tool
"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from common.models import ScanRequest
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "amass"
VERSION_CMD = ["amass", "-version"]

app = FastAPI()


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": TOOL_NAME}


@app.get("/version")
def version():
    """Get Amass version."""
    try:
        result = subprocess.run(
            VERSION_CMD,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {"version": result.stdout.strip() or result.stderr.strip(), "status": "success"}
    except Exception as e:
        logger.error(f"Failed to get version: {e}")
        return {"status": "error", "error": str(e)}, 500


@app.post("/scan")
def scan(request: ScanRequest):
    """Execute Amass enumeration scan."""
    try:
        # Get domain from config
        domain = ""
        if request.config:
            domain = request.config.get("domain") or request.config.get("target", "")

        if not domain:
            return {
                "status": "error",
                "error": "Domain is required in config (use 'domain' or 'target' field)",
            }

        # Generate timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"

        # Determine output directory
        parts = Path(request.workspace_path).parts
        if "workspaces" in parts:
            idx = parts.index("workspaces")
            if idx + 1 < len(parts):
                workspace_root = Path(*parts[: idx + 2])
                output_dir = workspace_root / "reports" / "reconnaissance" / TOOL_NAME
            else:
                output_dir = Path(request.workspace_path) / "reports" / "reconnaissance" / TOOL_NAME
        else:
            output_dir = Path(request.workspace_path).parent / "reports" / "reconnaissance" / TOOL_NAME

        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / f"{timestamp}.json"

        # Amass v5 stores results in a graph database, not a flat text file.
        # In v5 the `-o` flag only captures terminal stdout/stderr (the progress
        # bar) — NOT discovered names — and the old `amass db` subcommand was
        # removed. The correct flow is:
        #   1. `amass enum`  populates the engine's graph DB
        #   2. `amass subs -names`  reads discovered FQDNs back out of that DB
        # The amass *engine* owns a single graph DB at $HOME/.config/amass;
        # client-side `-dir`/`HOME` overrides do NOT relocate it, so both
        # commands use the default location and we scope results by `-d domain`.

        # Default timeout of 30 minutes to prevent indefinite hangs
        timeout_min = 30

        # Build enum command. `-silent` suppresses the progress bar that would
        # otherwise flood the logs; the graph DB is still populated.
        enum_cmd = ["amass", "enum", "-d", domain, "-silent", "-nocolor"]

        # Add optional parameters (note: `-passive` is the default in v5 and the
        # flag is deprecated, so it is intentionally not forwarded).
        if request.config:
            if request.config.get("active", False):
                enum_cmd.append("-active")
            if request.config.get("brute", False):
                enum_cmd.append("-brute")
            timeout_min = request.config.get("timeout", 30)
            if "max_dns_queries" in request.config:
                enum_cmd.extend(["-dns-qps", str(request.config["max_dns_queries"])])

        # amass -timeout is in minutes; it governs amass's own enumeration loop.
        enum_cmd.extend(["-timeout", str(timeout_min)])

        # Hard wall-clock ceiling on the subprocess itself: if amass ignores its
        # own -timeout (or hangs on network I/O), the request thread must not
        # block forever. Allow a 60s buffer over amass's internal timeout.
        subprocess_timeout = int(timeout_min) * 60 + 60

        # Execute enumeration (populates the graph DB)
        logger.info(f"Executing Amass scan: {' '.join(enum_cmd)}")
        try:
            subprocess.run(
                enum_cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=subprocess_timeout,
            )
        except subprocess.TimeoutExpired:
            # Not fatal: amass may have already written partial results to the
            # graph DB before the wall-clock ceiling fired. Fall through and try
            # to extract whatever was discovered.
            logger.warning(
                f"Amass enum hit the {subprocess_timeout}s wall-clock ceiling; "
                f"extracting any partial results from the graph DB."
            )

        # Extract discovered names from the graph DB via `amass subs -names`.
        subs_cmd = ["amass", "subs", "-names", "-d", domain, "-nocolor"]
        try:
            subs_result = subprocess.run(
                subs_cmd, capture_output=True, text=True, check=False, timeout=120
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": "Amass result extraction (amass subs) timed out",
            }

        # A non-zero exit from `amass subs` is not necessarily fatal — it also
        # occurs when simply no names were discovered. Log it but still attempt
        # to parse stdout (an empty result is a valid "0 findings" outcome).
        if subs_result.returncode != 0:
            logger.warning(
                f"amass subs exited {subs_result.returncode}: "
                f"{subs_result.stderr.strip()[:300]}"
            )

        # Each stdout line is a discovered FQDN. When nothing is found, amass
        # prints a human sentinel ("No names were discovered") instead — filter
        # that and any non-hostname noise (a valid FQDN has no spaces and a dot).
        subdomains = sorted(
            {
                line.strip()
                for line in subs_result.stdout.splitlines()
                if line.strip() and " " not in line.strip() and "." in line.strip()
            }
        )

        json_data = [{"subdomain": s} for s in subdomains]
        with open(json_path, "w") as f:
            json.dump(json_data, f, indent=2)

        finding_count = len(subdomains)
        logger.info(f"Amass discovered {finding_count} name(s) for {domain}")

        return {
            "status": "success",
            "finding_count": finding_count,
            "report_path": str(json_path),
            "timestamp": timestamp,
        }

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return {"status": "error", "error": str(e)}
