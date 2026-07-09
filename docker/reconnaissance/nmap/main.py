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

        scaninfo = root.find("scaninfo")
        if scaninfo is not None:
            result["scan_info"] = {
                "type": scaninfo.get("type", ""),
                "protocol": scaninfo.get("protocol", ""),
                "numservices": scaninfo.get("numservices", ""),
                "services": scaninfo.get("services", ""),
            }

        for host in root.findall("host"):
            host_data = {
                "status": {},
                "addresses": [],
                "hostnames": [],
                "ports": [],
                "os": {},
            }

            status = host.find("status")
            if status is not None:
                host_data["status"] = {
                    "state": status.get("state", ""),
                    "reason": status.get("reason", ""),
                }

            for address in host.findall("address"):
                host_data["addresses"].append(
                    {
                        "addr": address.get("addr", ""),
                        "addrtype": address.get("addrtype", ""),
                    }
                )

            hostnames = host.find("hostnames")
            if hostnames is not None:
                for hostname in hostnames.findall("hostname"):
                    host_data["hostnames"].append(
                        {
                            "name": hostname.get("name", ""),
                            "type": hostname.get("type", ""),
                        }
                    )

            ports = host.find("ports")
            if ports is not None:
                for port in ports.findall("port"):
                    port_data = {
                        "protocol": port.get("protocol", ""),
                        "portid": port.get("portid", ""),
                        "state": {},
                        "service": {},
                    }

                    state = port.find("state")
                    if state is not None:
                        port_data["state"] = {
                            "state": state.get("state", ""),
                            "reason": state.get("reason", ""),
                        }

                    service = port.find("service")
                    if service is not None:
                        port_data["service"] = {
                            "name": service.get("name", ""),
                            "product": service.get("product", ""),
                            "version": service.get("version", ""),
                            "extrainfo": service.get("extrainfo", ""),
                        }

                    host_data["ports"].append(port_data)

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
    target = ""
    if request.config:
        target = request.config.get("target", "")

    if not target:
        raise ValueError("Target is required in config for Nmap scan (use 'target' field)")

    xml_path = output_path.with_suffix(".xml")

    cmd = ["nmap", "-oX", str(xml_path)]

    config = request.config or {}

    host_timeout = f"{config['timeout']}s" if config.get("timeout") else "5m"
    cmd.extend(["--host-timeout", host_timeout])
    cmd.extend(["--max-retries", "2"])  # Limit retries

    # Timing template — default -T4 to finish within the MCP client timeout (~50s).
    timing = config.get("timing", 4)
    cmd.append(f"-T{timing}")

    # Default top-100 ports (not nmap's 1000) to stay within client timeout.
    ports = config.get("ports")
    if ports:
        cmd.extend(["-p", str(ports)])
    else:
        cmd.extend(["--top-ports", str(config.get("top_ports", 100))])

    if request.config:
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

        if request.config.get("service_version", False):
            cmd.append("-sV")

        # OS detection (WARNING: Can be very slow and may hang)
        if request.config.get("os_detection", False):
            cmd.append("-O")
            cmd.append("--osscan-limit")

        if request.config.get("aggressive", False):
            cmd.append("-A")

        scripts = request.config.get("scripts")
        if scripts:
            cmd.extend(["--script", scripts])

        if request.config.get("verbose", False):
            cmd.append("-v")

    cmd.append(target)

    logger.info(f"Built nmap command: {cmd}")
    return cmd


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
        full_scan_path = Path(request.workspace_path) / request.scan_path

        if not full_scan_path.exists():
            raise HTTPException(status_code=404, detail=f"Scan path does not exist: {full_scan_path}")

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"

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

        cmd = scan_cmd_builder(request, output_path)

        # bound it with a timeout (10-minute default, overridable per-request).
        timeout_seconds = (request.config or {}).get("timeout_seconds", 600)
        logger.info(f"Executing {TOOL_NAME} scan: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,  # Don't raise on non-zero exit code
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as e:
            logger.error(f"{TOOL_NAME} scan timed out after {timeout_seconds}s")
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            return {
                "status": "error",
                "error": f"Scan timed out after {timeout_seconds}s",
                "output": stdout,
            }

        xml_path = output_path.with_suffix(".xml")
        if not xml_path.exists():
            logger.error(f"Scan failed: {result.stderr}")
            return {
                "status": "error",
                "error": f"Scan failed to generate report. Stderr: {result.stderr}",
                "output": result.stdout,
            }

        logger.info(f"Converting XML to JSON: {xml_path} -> {output_path}")
        json_data = xml_to_json(xml_path)

        with open(output_path, "w") as f:
            json.dump(json_data, f, indent=2)

        logger.info(f"Successfully converted XML to JSON: {output_path}")

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
