"""HTTP service wrapper for Psalm SAST tool."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Psalm Service", version="1.0.0")


def log(message: str):
    """Log message to stderr so it shows up in docker logs."""
    print(f"[{datetime.utcnow().isoformat()}] {message}", file=sys.stderr)


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
        log(f"Received scan request for {full_scan_path}")

        if not full_scan_path.exists():
            log(f"Scan path does not exist: {full_scan_path}")
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
        log(f"Output path: {output_path}")

        # Psalm needs composer autoloading to resolve classes.
        # Install dependencies if composer.json exists but vendor/ doesn't.
        composer_json = full_scan_path / "composer.json"
        vendor_dir = full_scan_path / "vendor"
        
        if composer_json.exists() and not vendor_dir.exists():
            log("Running composer install (existing composer.json)...")
            result = subprocess.run(
                ["composer", "install", "--no-dev", "--no-scripts", "--no-interaction", "--ignore-platform-reqs"],
                capture_output=True,
                text=True,
                timeout=600,
                cwd=str(full_scan_path),
            )
            if result.returncode != 0:
                log(f"Composer install failed: {result.stderr}")
                log(f"Composer stdout: {result.stdout}")
                # We continue anyway, but log the error
            else:
                log("Composer install successful")

        # If there's no composer.json at all, create a minimal one so psalm --init works.
        if not composer_json.exists():
            log("Creating minimal composer.json...")
            composer_json.write_text('{"autoload":{"psr-4":{"":"./"}}}')
            result = subprocess.run(
                ["composer", "install", "--no-dev", "--no-scripts", "--no-interaction"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(full_scan_path),
            )
            if result.returncode != 0:
                log(f"Minimal composer install failed: {result.stderr}")

        # Psalm requires a psalm.xml config in the project root.
        psalm_config = full_scan_path / "psalm.xml"
        if not psalm_config.exists():
            log("Initializing psalm...")
            subprocess.run(
                ["psalm", "--init", ".", "3"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(full_scan_path),
            )

        # Build scan command
        # Psalm uses psalm.xml in cwd to determine project root and scan scope.
        # --report with .sarif extension auto-selects SARIF format.
        # --taint-analysis enables security scanning (SAST)
        cmd = [
            "psalm",
            f"--report={output_path}",
            "--no-cache",
            "--taint-analysis",
        ]

        # Add config options
        config = request.config or {}

        if "error_level" in config:
            cmd.append(f"--error-level={config['error_level']}")

        # Execute scan from the project directory so Psalm finds psalm.xml
        log(f"Executing scan command: {' '.join(cmd)}")
        start_time = datetime.utcnow()
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=900, cwd=str(full_scan_path)
        )
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        log(f"Scan completed in {duration}s with return code {result.returncode}")

        # Psalm returns non-zero exit codes when findings are found.
        # Only treat it as error if the output file wasn't created.
        if not output_path.exists():
            log(f"Output file not found. Stderr: {result.stderr}")
            log(f"Stdout: {result.stdout}")
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
            finding_count = sum(
                len(run.get("results", [])) for run in sarif_data.get("runs", [])
            )
            log(f"Findings count: {finding_count}")
        except Exception as e:
            log(f"Failed to parse SARIF: {e}")
            pass

        return {
            "status": "success",
            "output_path": str(output_path),
            "finding_count": finding_count,
            "duration_seconds": duration,
        }

    except subprocess.TimeoutExpired:
        log("Scan timed out")
        raise HTTPException(status_code=504, detail="Psalm scan timed out")
    except HTTPException:
        raise
    except Exception as e:
        log(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8087))
    uvicorn.run(app, host="0.0.0.0", port=port)
