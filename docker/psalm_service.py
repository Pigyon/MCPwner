"""HTTP service wrapper for Psalm SAST tool."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Psalm Service", version="1.0.0")


# Request/Response Models
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
    return {"status": "healthy", "service": "psalm"}


@app.get("/version", response_model=VersionResponse)
def version():
    """Get Psalm version."""
    try:
        result = subprocess.run(
            ["psalm", "--version"],
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
    Execute Psalm scan on a workspace.

    Returns scan results including finding count and report path.
    """
    try:
        # Build full scan path
        full_scan_path = Path(request.workspace_path) / request.scan_path

        if not full_scan_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Scan path does not exist: {full_scan_path}",
            )

        # Create output directory
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3] + "Z"
        workspace_base = Path(request.workspace_path).parent
        output_dir = workspace_base / "reports" / "sast" / "psalm"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}.sarif"

        # Build Psalm command
        # Psalm requires initialization if psalm.xml doesn't exist
        psalm_config = full_scan_path / "psalm.xml"
        if not psalm_config.exists():
            # Initialize Psalm with default config
            init_result = subprocess.run(
                ["psalm", "--init", str(full_scan_path), "3"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(full_scan_path),
            )
            # Psalm init may fail if no PHP files found, continue anyway

        # Build scan command
        cmd = [
            "psalm",
            "--report=" + str(output_path),
            "--output-format=sarif",
            "--no-cache",
        ]

        # Add config options
        config = request.config or {}

        # Add error level if specified
        if "error_level" in config:
            cmd.append(f"--error-level={config['error_level']}")

        # Add path to scan
        cmd.append(str(full_scan_path))

        # Execute scan
        start_time = datetime.utcnow()
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600, cwd=str(full_scan_path)
        )
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Psalm returns non-zero exit codes when findings are found
        # Only treat it as error if the output file wasn't created
        if not output_path.exists():
            raise HTTPException(
                status_code=500,
                detail={
                    "error": f"Psalm scan failed: {result.stderr}",
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
        raise HTTPException(status_code=504, detail="Psalm scan timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8087))
    uvicorn.run(app, host="0.0.0.0", port=port)
