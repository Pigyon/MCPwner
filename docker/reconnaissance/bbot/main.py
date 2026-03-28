"""
bbot Service - OSINT Automation Framework

bbot is a recursive, modular OSINT framework. It requires either a preset (-p),
flags (-f), or specific modules (-m) to run meaningful scans. Without them,
it only performs basic DNS resolution.

Config options:
  - target (required): Domain, IP, URL, or CIDR to scan
  - preset: One or more preset names as a comma/space-separated string, or the
            special value "deep" which stacks all heavy presets with aggressive flags.
            Available presets: subdomain-enum, cloud-enum, code-enum, email-enum,
            spider, web-basic, web-thorough, paramminer, web-screenshots, baddns-intense,
            kitchen-sink.
            Default when nothing specified: "subdomain-enum"
            Examples:
              "subdomain-enum"
              "subdomain-enum,web-basic"
              "subdomain-enum,cloud-enum,web-thorough"
              "deep"  (equivalent to all heavy presets + aggressive flag)
  - flags: Space-separated flag names (e.g. "safe passive", "aggressive")
  - modules: Space-separated module names (e.g. "httpx portscan sslcert")
  - output_modules: Space-separated output module names (default: "json")
  - require_flags: Only enable modules with these flags (e.g. "passive")
  - exclude_flags: Exclude modules with these flags (e.g. "slow")
  - exclude_modules: Exclude specific modules (e.g. "ipneighbor")
  - allow_deadly: Enable highly aggressive modules (boolean, default: false)
  - strict_scope: Only scan the exact target, not subdomains (boolean)
  - fast_mode: Scan only provided targets with no extra discovery (boolean)
"""

import json
import logging
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from common.models import HealthResponse, ScanRequest, VersionResponse
from fastapi import FastAPI, HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_NAME = "bbot"
VERSION_CMD = ["bbot", "--version"]

app = FastAPI(title="Bbot Service", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy", "service": TOOL_NAME}


@app.get("/version", response_model=VersionResponse)
def version():
    try:
        result = subprocess.run(VERSION_CMD, capture_output=True, text=True, timeout=5, check=True)
        return {"version": result.stdout.strip(), "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/modules")
def list_modules():
    """List all available bbot modules, presets, and flags."""
    try:
        modules_result = subprocess.run(
            ["bbot", "-l"], capture_output=True, text=True, timeout=15, check=False
        )
        presets_result = subprocess.run(
            ["bbot", "--list-presets"], capture_output=True, text=True, timeout=15, check=False
        )
        return {
            "status": "success",
            "modules": modules_result.stdout.strip(),
            "presets": presets_result.stdout.strip(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Presets stacked for a "deep" scan — everything meaningful without requiring API keys
DEEP_PRESETS = [
    "subdomain-enum",
    "cloud-enum",
    "email-enum",
    "spider",
    "web-thorough",
    "paramminer",
    "web-screenshots",
    "baddns-intense",
]


def _parse_presets(preset_value: str) -> List[str]:
    """Parse a preset string into a list, supporting comma or space separation."""
    # Replace commas with spaces then split
    return [p.strip() for p in preset_value.replace(",", " ").split() if p.strip()]


def _build_bbot_cmd(
    target: str,
    output_dir: str,
    scan_name: str,
    config: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Build the bbot CLI command.

    bbot writes output to {output_dir}/{scan_name}/ with files like output.json.
    We always pass -y (skip confirmation) and --no-deps (pre-installed in image).
    """
    cmd = [
        "bbot",
        "-t", target,
        "-o", output_dir,
        "-n", scan_name,
        "-y",
        "--no-deps",
    ]

    if not config:
        config = {}

    preset_raw = config.get("preset", "")
    has_flags = bool(config.get("flags"))
    has_modules = bool(config.get("modules"))

    if not preset_raw and not has_flags and not has_modules:
        # Default: subdomain enumeration
        cmd.extend(["-p", "subdomain-enum"])
    elif preset_raw == "deep":
        # Deep scan: stack all heavy presets + aggressive flag
        cmd.extend(["-p"] + DEEP_PRESETS)
        cmd.extend(["-f", "aggressive"])
    else:
        if preset_raw:
            presets = _parse_presets(preset_raw)
            cmd.extend(["-p"] + presets)
        if has_flags:
            cmd.extend(["-f"] + config["flags"].split())
        if has_modules:
            cmd.extend(["-m"] + config["modules"].split())

    # Output modules — default to json
    output_modules = config.get("output_modules", "json")
    cmd.extend(["-om"] + output_modules.split())

    # Filtering options
    if config.get("require_flags"):
        cmd.extend(["-rf"] + config["require_flags"].split())
    if config.get("exclude_flags"):
        cmd.extend(["-ef"] + config["exclude_flags"].split())
    if config.get("exclude_modules"):
        cmd.extend(["-em"] + config["exclude_modules"].split())

    # Boolean flags
    if config.get("allow_deadly"):
        cmd.append("--allow-deadly")
    if config.get("strict_scope"):
        cmd.append("--strict-scope")
    if config.get("fast_mode"):
        cmd.append("--fast-mode")

    return cmd


def _summarize_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a structured summary of bbot events for LLM consumption."""
    by_type: Dict[str, list] = {}
    for ev in events:
        etype = ev.get("type", "UNKNOWN")
        by_type.setdefault(etype, []).append(ev)

    subdomains = sorted({ev.get("data", "") for ev in by_type.get("DNS_NAME", []) if ev.get("data")})
    ips = sorted({ev.get("data", "") for ev in by_type.get("IP_ADDRESS", []) if ev.get("data")})
    open_ports = sorted(
        {ev.get("data", "") for ev in by_type.get("OPEN_TCP_PORT", []) if ev.get("data")}
    )
    urls = sorted({ev.get("data", "") for ev in by_type.get("URL", []) if ev.get("data")})
    techs = sorted(
        {
            ev.get("data", {}).get("technology", ev.get("data", ""))
            for ev in by_type.get("TECHNOLOGY", [])
            if ev.get("data")
        }
    )
    vulns = [
        {
            "name": ev.get("data", {}).get("description", ev.get("data", "")),
            "severity": ev.get("data", {}).get("severity", "unknown"),
            "host": ev.get("data", {}).get("host", ""),
        }
        for ev in by_type.get("VULNERABILITY", [])
    ]
    findings = [
        {
            "description": ev.get("data", {}).get("description", str(ev.get("data", ""))),
            "host": ev.get("data", {}).get("host", ""),
        }
        for ev in by_type.get("FINDING", [])
    ]
    emails = sorted({ev.get("data", "") for ev in by_type.get("EMAIL_ADDRESS", []) if ev.get("data")})
    storage = sorted(
        {ev.get("data", {}).get("url", str(ev.get("data", ""))) for ev in by_type.get("STORAGE_BUCKET", []) if ev.get("data")}
    )

    event_type_counts = {k: len(v) for k, v in sorted(by_type.items())}

    # Suggest next steps based on what was found
    next_steps = []
    if subdomains and len(subdomains) > 1:
        next_steps.append(
            "Run 'web-basic' or 'web-thorough' preset against discovered subdomains for HTTP probing and vuln detection"
        )
    if open_ports:
        next_steps.append(
            "Run 'nuclei' preset against discovered URLs/ports for vulnerability scanning"
        )
    if urls and not vulns:
        next_steps.append(
            "Run 'web-thorough' or 'paramminer' preset to find hidden parameters and web vulnerabilities"
        )
    if not next_steps:
        next_steps.append(
            "Run 'subdomain-enum,web-basic' to discover subdomains and probe web services"
        )

    return {
        "event_type_counts": event_type_counts,
        "subdomains": subdomains[:50],
        "ip_addresses": ips[:50],
        "open_ports": open_ports[:50],
        "urls": urls[:50],
        "technologies": techs[:30],
        "vulnerabilities": vulns[:30],
        "findings": findings[:30],
        "emails": emails[:30],
        "storage_buckets": storage[:20],
        "suggested_next_steps": next_steps,
    }


@app.post("/scan")
def scan(request: ScanRequest):
    """Execute a bbot scan.

    bbot manages its own output directory structure:
      {output_dir}/{scan_name}/output.json

    After the scan, we copy the JSON output to the standard MCPwner report path.
    """
    try:
        config = request.config or {}
        target = config.get("target", "").strip()
        if not target:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Missing required field: 'target'. "
                    "Pass config={'target': 'example.com', 'preset': 'subdomain-enum'}. "
                    f"Received config: {config!r}"
                ),
            )

        # Determine workspace root and report output path
        parts = Path(request.workspace_path).parts
        if "workspaces" in parts:
            idx = parts.index("workspaces")
            if idx + 1 < len(parts):
                workspace_root = Path(*parts[: idx + 2])
            else:
                workspace_root = Path(request.workspace_path)
        else:
            workspace_root = Path(request.workspace_path).parent

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        report_dir = workspace_root / "reports" / "reconnaissance" / "bbot"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"{timestamp}.json"

        # bbot writes to its own directory structure
        bbot_output_dir = str(workspace_root / "tmp" / "bbot")
        scan_name = f"scan_{timestamp}"

        cmd = _build_bbot_cmd(
            target=target,
            output_dir=bbot_output_dir,
            scan_name=scan_name,
            config=config,
        )

        logger.info(f"Executing bbot scan: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        # bbot writes JSON output to {output_dir}/{scan_name}/output.json
        bbot_json = Path(bbot_output_dir) / scan_name / "output.json"

        if not bbot_json.exists():
            logger.error(f"bbot output not found at {bbot_json}")
            logger.error(f"stdout: {result.stdout[-2000:] if result.stdout else 'empty'}")
            logger.error(f"stderr: {result.stderr[-2000:] if result.stderr else 'empty'}")
            return {
                "status": "error",
                "error": f"bbot scan did not produce output. stderr: {result.stderr[-500:] if result.stderr else 'none'}",
                "stdout": result.stdout[-1000:] if result.stdout else "",
            }

        # Copy bbot's output to the standard report path
        shutil.copy2(str(bbot_json), str(report_path))

        # Parse events and build a structured summary for the LLM
        events = []
        try:
            with open(report_path, "r") as f:
                events = [json.loads(line) for line in f if line.strip()]
            # Persist as JSON array
            with open(report_path, "w") as f:
                json.dump(events, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not parse bbot output: {e}")

        summary = _summarize_events(events)

        return {
            "status": "success",
            "target": target,
            "preset_used": config.get("preset", "subdomain-enum"),
            "finding_count": len(events),
            "report_path": str(report_path),
            "timestamp": timestamp,
            "summary": summary,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("bbot scan execution error")
        raise HTTPException(status_code=500, detail=str(e))
