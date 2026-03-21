"""
Nmap Service - Network Scanner for Host and Service Discovery
"""

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import defusedxml.ElementTree as ET
from common.models import HealthResponse, ScanRequest, VersionResponse
from fastapi import FastAPI, HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "nmap"
VERSION_CMD = ["nmap", "--version"]


def xml_to_json(xml_path: Path) -> Dict[str, Any]:
    """Convert Nmap XML output to JSON format."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        result = {
            "scanner": root.get("scanner", "nmap"),
            "version": root.get("version", ""),
            "scan_info": {},
            "hosts": [],
        }

        # Parse scan info
        scaninfo = root.find("scaninfo")
        if scaninfo is not None:
            result["scan_info"] = {
                "type": scaninfo.get("type", ""),
                "protocol": scaninfo.get("protocol", ""),
                "numservices": scaninfo.get("numservices", ""),
                "services": scaninfo.get("services", ""),
            }

        # Parse hosts
        for host in root.findall("host"):
            host_data = {
                "status": {},
                "addresses": [],
                "hostnames": [],
                "ports": [],
                "os": {},
            }

            # Status
            status = host.find("status")
            if status is not None:
                host_data["status"] = {
                    "state": status.get("state", ""),
                    "reason": status.get("reason", ""),
                }

            # Addresses
            for address in host.findall("address"):
                host_data["addresses"].append(
                    {
                        "addr": address.get("addr", ""),
                        "addrtype": address.get("addrtype", ""),
                    }
                )

            # Hostnames
            hostnames = host.find("hostnames")
            if hostnames is not None:
                for hostname in hostnames.findall("hostname"):
                    host_data["hostnames"].append(
                        {
                            "name": hostname.get("name", ""),
                            "type": hostname.get("type", ""),
                        }
                    )

            # Ports
            ports = host.find("ports")
            if ports is not None:
                for port in ports.findall("port"):
                    port_data = {
                        "protocol": port.get("protocol", ""),
                        "portid": port.get("portid", ""),
                        "state": {},
                        "service": {},
                    }

                    # Port state
                    state = port.find("state")
                    if state is not None:
                        port_data["state"] = {
                            "state": state.get("state", ""),
                            "reason": state.get("reason", ""),
                        }

                    # Service info
                    service = port.find("service")
                    if service is not None:
                        port_data["service"] = {
                            "name": service.get("name", ""),
                            "product": service.get("product", ""),
                            "version": service.get("version", ""),
                            "extrainfo": service.get("extrainfo", ""),
                        }

                    host_data["ports"].append(port_data)

            # OS detection
            os_elem = host.find("os")
            if os_elem is not None:
                osmatch = os_elem.find("osmatch")
                if osmatch is not None:
                    host_data["os"] = {
                        "name": osmatch.get("name", ""),
                        "accuracy": osmatch.get("accuracy", ""),
                    }

            result["hosts"].append(host_data)

        return result

    except ET.ParseError as e:
        logger.error(f"Failed to parse XML: {e}")
        raise ValueError(f"Invalid XML output from Nmap: {e}")
    except Exception as e:
        logger.error(f"Error converting XML to JSON: {e}")
        raise


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    """Build Nmap scan command."""
    # Get target from config
    target = ""
    if request.config:
        target = request.config.get("target", "")

    if not target:
        raise ValueError("Target is required in config for Nmap scan (use 'target' field)")

    # Nmap outputs XML first, then we convert to JSON
    xml_path = output_path.with_suffix(".xml")

    # Basic Nmap command with XML output
    cmd = ["nmap", "-oX", str(xml_path)]

    # Add default timeouts to prevent hangs
    cmd.extend(["--host-timeout", "5m"])  # 5 minute timeout per host
    cmd.extend(["--max-retries", "2"])  # Limit retries

    # Add optional parameters
    if request.config:
        # Scan type
        scan_type = request.config.get("scan_type")
        if scan_type == "tcp_connect":
            cmd.append("-sT")  # TCP connect scan (no root required)
        elif scan_type == "udp":
            cmd.append("-sU")  # UDP scan
        elif scan_type == "syn":
            cmd.append("-sS")  # SYN stealth scan (requires root)
        elif scan_type == "ack":
            cmd.append("-sA")  # ACK scan (for firewall detection)
        elif scan_type == "window":
            cmd.append("-sW")  # Window scan
        elif scan_type == "null":
            cmd.append("-sN")  # Null scan
        elif scan_type == "fin":
            cmd.append("-sF")  # FIN scan
        elif scan_type == "xmas":
            cmd.append("-sX")  # Xmas scan
        # If no scan_type specified, nmap defaults to -sS (SYN) when run as root

        # Port specification
        ports = request.config.get("ports")
        if ports:
            cmd.extend(["-p", str(ports)])

        # Service version detection
        if request.config.get("service_version", False):
            cmd.append("-sV")

        # OS detection (WARNING: Can be very slow and may hang)
        if request.config.get("os_detection", False):
            cmd.append("-O")
            # Add --osscan-limit to skip OS detection if no open/closed ports
            cmd.append("--osscan-limit")

        # Aggressive scan (enables OS detection, version detection, script scanning, and traceroute)
        if request.config.get("aggressive", False):
            cmd.append("-A")

        # Timing template (0-5, where 5 is fastest)
        timing = request.config.get("timing")
        if timing is not None:
            cmd.append(f"-T{timing}")

        # Script scanning
        scripts = request.config.get("scripts")
        if scripts:
            cmd.extend(["--script", scripts])

        # Verbose output
        if request.config.get("verbose", False):
            cmd.append("-v")

    # Add target
    cmd.append(target)

    logger.info(f"Built nmap command: {cmd}")
    return cmd


# Create custom FastAPI app with XML to JSON conversion
app = FastAPI(title="Nmap Service", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": TOOL_NAME}


@app.get("/version", response_model=VersionResponse)
def version():
    """Get tool version."""
    try:
        result = subprocess.run(
            VERSION_CMD,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return {"version": result.stdout.strip(), "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan")
def scan(request: ScanRequest):
    """
    Execute Nmap scan on a workspace.
    """
    try:
        # Build full scan path
        full_scan_path = Path(request.workspace_path) / request.scan_path

        if not full_scan_path.exists():
            raise HTTPException(status_code=404, detail=f"Scan path does not exist: {full_scan_path}")

        # Create output directory
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"

        # Extract workspace root
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
        output_path = output_dir / f"{timestamp}.json"

        # Build command (will create XML file)
        cmd = scan_cmd_builder(request, output_path)

        # Execute scan
        logger.info(f"Executing {TOOL_NAME} scan: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,  # Don't raise on non-zero exit code
        )

        # Check if XML report was created
        xml_path = output_path.with_suffix(".xml")
        if not xml_path.exists():
            logger.error(f"Scan failed: {result.stderr}")
            return {
                "status": "error",
                "error": f"Scan failed to generate report. Stderr: {result.stderr}",
                "output": result.stdout,
            }

        # Convert XML to JSON
        logger.info(f"Converting XML to JSON: {xml_path} -> {output_path}")
        json_data = xml_to_json(xml_path)

        # Write JSON output
        with open(output_path, "w") as f:
            json.dump(json_data, f, indent=2)

        logger.info(f"Successfully converted XML to JSON: {output_path}")

        # Count findings (hosts with open ports)
        finding_count = 0
        for host in json_data.get("hosts", []):
            if host.get("ports"):
                finding_count += len(
                    [p for p in host["ports"] if p.get("state", {}).get("state") == "open"]
                )

        return {
            "status": "success",
            "finding_count": finding_count,
            "report_path": str(output_path),
            "timestamp": timestamp,
        }

    except Exception as e:
        logger.exception("Scan execution error")
        raise HTTPException(status_code=500, detail=str(e))
