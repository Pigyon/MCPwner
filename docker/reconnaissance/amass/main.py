"""
Amass Service - Network Mapping and Attack Surface Discovery Tool
"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from common.models import ScanRequest
from fastapi import FastAPI, HTTPException

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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan")
def scan(request: ScanRequest):
    """Execute Amass enumeration scan."""
    try:
        domain = ""
        if request.config:
            domain = request.config.get("domain") or request.config.get("target", "")

        if not domain:
            return {
                "status": "error",
                "error": "Domain is required in config (use 'domain' or 'target' field)",
            }

        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"

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

        # Amass v5: enum populates a graph DB; subs -names reads FQDNs (-o only captures stdout).
        timeout_min = 30

        enum_cmd = ["amass", "enum", "-d", domain, "-silent", "-nocolor"]

        if request.config:
            if request.config.get("active", False):
                enum_cmd.append("-active")
            if request.config.get("brute", False):
                enum_cmd.append("-brute")
            timeout_min = request.config.get("timeout", 30)
            if "max_dns_queries" in request.config:
                enum_cmd.extend(["-dns-qps", str(request.config["max_dns_queries"])])

        enum_cmd.extend(["-timeout", str(timeout_min)])

        # Wall-clock ceiling with 60s buffer over amass's internal -timeout (minutes).
        subprocess_timeout = int(timeout_min) * 60 + 60

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
            # Partial graph DB results may exist after a wall-clock timeout.
            logger.warning(
                f"Amass enum hit the {subprocess_timeout}s wall-clock ceiling; "
                f"extracting any partial results from the graph DB."
            )

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

        if subs_result.returncode != 0:
            logger.warning(
                f"amass subs exited {subs_result.returncode}: {subs_result.stderr.strip()[:300]}"
            )

        # Filter amass's "No names were discovered" sentinel and non-FQDN noise.
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
