import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from common.models import HealthResponse, ScanRequest, VersionResponse
from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)

app = FastAPI(title="Joern Service", version="1.0.0")

SCAN_SCRIPT = "/service/scan.sc"


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "healthy", "service": "joern"}


@app.get("/version", response_model=VersionResponse)
def version():
    try:
        result = subprocess.run(
            ["joern", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        return {"version": result.stdout.strip(), "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scan")
def scan(request: ScanRequest):
    try:
        full_scan_path = Path(request.workspace_path) / request.scan_path

        if not full_scan_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Scan path does not exist: {full_scan_path}"
            )

        # Build output path
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        parts = Path(request.workspace_path).parts
        if "workspaces" in parts:
            idx = parts.index("workspaces")
            if idx + 1 < len(parts):
                workspace_root = Path(*parts[: idx + 2])
                output_dir = workspace_root / "reports" / "sast" / "joern"
            else:
                output_dir = Path(request.workspace_path) / "reports" / "sast" / "joern"
        else:
            output_dir = Path(request.workspace_path).parent / "reports" / "sast" / "joern"

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}.json"

        config = request.config or {}

        # Determine scan mode: joern-scan (quick, uses query DB) or joern --script (custom)
        use_scan = config.get("mode", "scan") == "scan"

        if use_scan:
            # Use joern-scan for automated scanning with the query database
            cmd = ["joern-scan", str(full_scan_path), "--overwrite"]

            if "tags" in config:
                cmd.extend(["--tags", config["tags"]])

            if "names" in config:
                cmd.extend(["--names", config["names"]])

            logger.info(f"Executing joern-scan: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            # Parse joern-scan text output into JSON
            findings = _parse_joern_scan_output(result.stdout)
            with open(output_path, "w") as f:
                json.dump(findings, f, indent=2)

            finding_count = len(findings)
        else:
            # Use joern --script for custom CPG analysis
            cmd = [
                "joern",
                "--script",
                SCAN_SCRIPT,
                "--param",
                f"inputPath={full_scan_path}",
                "--param",
                f"outFile={output_path}",
            ]

            logger.info(f"Executing joern script: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if not output_path.exists():
                return {
                    "status": "error",
                    "error": f"Joern script failed to generate report. Stderr: {result.stderr}",
                    "output": result.stdout,
                }

            with open(output_path, "r") as f:
                data = json.load(f)
            finding_count = len(data) if isinstance(data, list) else 0

        return {
            "status": "success",
            "finding_count": finding_count,
            "report_path": str(output_path),
            "timestamp": timestamp,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Scan execution error")
        raise HTTPException(status_code=500, detail=str(e))


def _parse_joern_scan_output(output: str) -> list:
    """Parse joern-scan text output into structured JSON.

    joern-scan output format:
    Result: <score> : <title>: <filepath>:<line>:<function>
    """
    findings = []
    for line in output.strip().splitlines():
        line = line.strip()
        if not line.startswith("Result:"):
            continue
        try:
            # "Result: 8.0 : Dangerous function gets() used: /path/file.c:6:main"
            rest = line[len("Result:"):].strip()
            score_str, rest = rest.split(":", 1)
            score = float(score_str.strip())
            # rest = " Dangerous function gets() used: /path/file.c:6:main"
            # Split from the right to handle colons in the title
            parts = rest.rsplit(":", 3)
            if len(parts) >= 4:
                title_and_path = parts[0]
                # The last colon-separated segment before line:func is the filepath
                # title_and_path = " Dangerous function gets() used: /path/file.c"
                tp_parts = title_and_path.rsplit(":", 1)
                title = tp_parts[0].strip() if len(tp_parts) > 1 else title_and_path.strip()
                filepath = tp_parts[1].strip() if len(tp_parts) > 1 else ""
                line_number = parts[1].strip()
                function_name = parts[2].strip()
            else:
                title = rest.strip()
                filepath = ""
                line_number = ""
                function_name = ""

            findings.append({
                "score": score,
                "title": title,
                "filepath": filepath,
                "line": line_number,
                "function": function_name,
            })
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse joern-scan line: {line}: {e}")
            continue

    return findings
