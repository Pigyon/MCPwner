"""
Dalfox DAST service — XSS and open-redirect scanner.

Dalfox outputs native JSON. When the target is unreachable or no XSS is found
it writes `[{}]` (a list with one empty object). The wrapper filters that out
so the report is a clean empty list when there are no findings.

Config options:
  - target (required): URL to scan for reflected/stored XSS
  - cookie: Cookie header value (e.g. "PHPSESSID=abc; security=low")
  - header: Extra HTTP header (e.g. "Authorization: Bearer token")
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from common.base_service import create_scanner_app
from common.models import ScanRequest

TOOL_NAME = "dalfox"
VERSION_CMD = ["dalfox", "version"]


def scan_cmd_builder(request: ScanRequest, output_path: Path) -> List[str]:
    config: Dict[str, Any] = request.config or {}
    target = str(config.get("target", "")).strip()
    if not target:
        raise ValueError("target is required")
    cmd = ["dalfox", "url", target, "--format", "json", "-o", str(output_path), "--silence"]
    if config.get("cookie"):
        cmd.extend(["--cookie", str(config["cookie"])])
    if config.get("header"):
        cmd.extend(["--header", str(config["header"])])
    return cmd


app = create_scanner_app(
    tool_name=TOOL_NAME,
    version_cmd=VERSION_CMD,
    scan_cmd_builder=scan_cmd_builder,
    report_format="json",
    tool_category="dast",
)

_original_scan = None
for route in app.routes:
    if hasattr(route, "endpoint") and route.path == "/scan":
        _original_scan = route.endpoint
        break


@app.post("/scan")
def scan_with_cleanup(request: ScanRequest):
    result = _original_scan(request)
    if isinstance(result, dict) and result.get("status") == "success":
        report_path = Path(result.get("report_path", ""))
        if report_path.exists():
            try:
                with open(report_path, "r") as fh:
                    data = json.load(fh)
                if isinstance(data, list):
                    cleaned = [entry for entry in data if isinstance(entry, dict) and len(entry) > 0]
                    with open(report_path, "w") as fh:
                        json.dump(cleaned, fh, indent=2)
                    result["finding_count"] = len(cleaned)
            except Exception:
                pass
    return result
