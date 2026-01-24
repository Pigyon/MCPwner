"""HTTP service wrapper for PMD SAST tool."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="PMD Service", version="1.0.0")


# Request/Response Models
class ScanConfig(BaseModel):
    rulesets: Optional[List[str]] = None
    language: Optional[str] = None
    exclude: Optional[List[str]] = None


class ScanRequest(BaseModel):
    workspace_path: str
    scan_path: Optional[str] = "."
    config: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    service: str


class VersionResponse(BaseModel):
    version: str
    status: str


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "pmd"}


@app.get("/version", response_model=VersionResponse)
def version():
    """Get PMD version."""
    try:
        result = subprocess.run(
            ["pmd", "--version"],
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
    Execute PMD scan on a workspace.

    Returns scan results including finding count and report path.
    """
    try:
        # Build full scan path
        full_scan_path = Path(request.workspace_path) / request.scan_path

        if not full_scan_path.exists():
            raise HTTPException(status_code=404, detail=f"Scan path does not exist: {full_scan_path}")

        # Create output directory
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        workspace_base = Path(request.workspace_path).parent
        output_dir = workspace_base / "reports" / "sast" / "pmd"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}.sarif"

        # Build PMD command
        # PMD 7.x uses: pmd check --dir <path> --rulesets <rulesets>
        # --format sarif --report-file <output>
        cmd = [
            "pmd",
            "check",
            "--dir",
            str(full_scan_path),
            "--format",
            "sarif",
            "--report-file",
            str(output_path),
        ]

        # Add config options
        config = request.config or {}

        # Add rulesets
        if "rulesets" in config and config["rulesets"]:
            rulesets = ",".join(config["rulesets"])
            cmd.extend(["--rulesets", rulesets])
        else:
            # Default to security rulesets for common languages
            cmd.extend(
                [
                    "--rulesets",
                    "category/java/security.xml,category/apex/security.xml",
                ]
            )

        # Add language-specific configuration
        if "language" in config:
            # PMD auto-detects languages, but we can use --use-version
            # for specific language versions
            pass  # Language is handled by file extensions

        # Execute scan
        start_time = datetime.utcnow()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # PMD returns non-zero exit codes when findings are found (exit code 4)
        # Only treat it as error if the output file wasn't created
        if not output_path.exists():
            raise HTTPException(
                status_code=500,
                detail={
                    "error": f"PMD scan failed: {result.stderr}",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )

        # Parse SARIF to count findings
        finding_count = 0
        try:
            with open(output_path, "r") as f:
                sarif_data = json.load(f)
            finding_count = sum(len(run.get("results", [])) for run in sarif_data.get("runs", []))
        except Exception:
            # If we can't parse SARIF, still return success but with 0 findings
            pass

        return {
            "status": "success",
            "output_path": str(output_path),
            "finding_count": finding_count,
            "duration_seconds": duration,
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="PMD scan timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8086))
    uvicorn.run(app, host="0.0.0.0", port=port)
