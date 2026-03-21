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

        # Amass outputs text, we'll convert to JSON
        txt_path = output_dir / f"{timestamp}.txt"
        json_path = output_dir / f"{timestamp}.json"

        # Build Amass command
        cmd = ["amass", "enum", "-d", domain, "-o", str(txt_path)]

        # Add optional parameters
        if request.config:
            if request.config.get("passive", False):
                cmd.append("-passive")
            if request.config.get("brute", False):
                cmd.append("-brute")
            if "timeout" in request.config:
                cmd.extend(["-timeout", str(request.config["timeout"])])
            if "max_dns_queries" in request.config:
                cmd.extend(["-max-dns-queries", str(request.config["max_dns_queries"])])

        # Execute scan
        logger.info(f"Executing Amass scan: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        # Check if text output was created
        if not txt_path.exists():
            logger.error(f"Scan failed: {result.stderr}")
            return {
                "status": "error",
                "error": f"Scan failed to generate report. Stderr: {result.stderr}",
                "output": result.stdout,
            }

        # Convert text output to JSON
        try:
            with open(txt_path, "r") as f:
                subdomains = [line.strip() for line in f if line.strip()]

            json_data = [{"subdomain": subdomain} for subdomain in subdomains]

            with open(json_path, "w") as f:
                json.dump(json_data, f, indent=2)

            finding_count = len(subdomains)
            logger.info(f"Converted {finding_count} subdomains to JSON format")

            # Remove temporary text file
            txt_path.unlink()

        except Exception as e:
            logger.error(f"Failed to convert output to JSON: {e}")
            return {
                "status": "error",
                "error": f"Failed to convert output: {e}",
            }

        return {
            "status": "success",
            "finding_count": finding_count,
            "report_path": str(json_path),
            "timestamp": timestamp,
        }

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return {"status": "error", "error": str(e)}
