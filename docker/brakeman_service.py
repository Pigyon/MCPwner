"""HTTP service wrapper for Brakeman SAST tool."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Brakeman Service", version="1.0.0")


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
    return {"status": "healthy", "service": "brakeman"}


@app.get("/version", response_model=VersionResponse)
def version():
    """Get Brakeman version."""
    try:
        result = subprocess.run(
            ["brakeman", "--version"],
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
    Execute Brakeman scan on a workspace.

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
        output_dir = workspace_base / "reports" / "sast" / "brakeman"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}.sarif"

        # Build brakeman command
        # Brakeman expects to be run from the Rails app root
        cmd = ["brakeman", "-f", "sarif", "-o", str(output_path)]

        # Add config options
        config = request.config or {}

        # Add confidence level filter if specified
        if "confidence" in config and config["confidence"]:
            confidence_levels = config["confidence"]
            if isinstance(confidence_levels, list):
                # Map confidence levels to Brakeman's -w flag (warning levels)
                # Brakeman uses confidence levels: 0 (high), 1 (medium), 2 (weak/low)
                min_confidence = min(
                    [{"high": 0, "medium": 1, "low": 2}.get(c.lower(), 2) for c in confidence_levels]
                )
                cmd.extend(["-w", str(min_confidence)])

        # Add path to scan (Rails app directory)
        cmd.extend(["-p", str(full_scan_path)])

        # Execute scan
        start_time = datetime.utcnow()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Brakeman returns non-zero exit codes when findings are found
        # Only treat it as error if the output file wasn't created
        if not output_path.exists():
            raise HTTPException(
                status_code=500,
                detail={
                    "error": f"Brakeman scan failed: {result.stderr}",
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
        raise HTTPException(status_code=504, detail="Brakeman scan timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8085))
    uvicorn.run(app, host="0.0.0.0", port=port)
