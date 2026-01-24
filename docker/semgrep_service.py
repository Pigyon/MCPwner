"""HTTP service wrapper for Semgrep SAST tool."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

app = FastAPI(title="Semgrep Service", version="1.0.0")


# Request/Response Models
class ScanConfig(BaseModel):
    rules: Optional[List[str]] = None
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


@app.get('/health', response_model=HealthResponse)
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "semgrep"}


@app.get('/version', response_model=VersionResponse)
def version():
    """Get Semgrep version."""
    try:
        result = subprocess.run(
            ["semgrep", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
        
        return {
            "version": result.stdout.strip(),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/scan')
def scan(request: ScanRequest):
    """
    Execute Semgrep scan on a workspace.
    
    Returns scan results including finding count and report path.
    """
    try:
        # Build full scan path
        full_scan_path = Path(request.workspace_path) / request.scan_path
        
        if not full_scan_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Scan path does not exist: {full_scan_path}"
            )
        
        # Create output directory
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S-%f')[:-3] + 'Z'
        workspace_base = Path(request.workspace_path).parent
        output_dir = workspace_base / 'reports' / 'sast' / 'semgrep'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f'{timestamp}.sarif'
        
        # Build semgrep command
        cmd = ['semgrep', 'scan', '--sarif', '--output', str(output_path)]
        
        # Add config options
        config = request.config or {}
        if 'rules' in config:
            for rule in config['rules']:
                cmd.extend(['--config', rule])
        else:
            # Default to auto config if no rules specified
            cmd.extend(['--config', 'auto'])
        
        # Add exclude patterns
        if 'exclude' in config:
            for pattern in config['exclude']:
                cmd.extend(['--exclude', pattern])
        
        cmd.append(str(full_scan_path))
        
        # Execute scan
        start_time = datetime.utcnow()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600
        )
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Semgrep returns non-zero exit codes when findings are found
        # Only treat it as error if the output file wasn't created
        if not output_path.exists():
            raise HTTPException(
                status_code=500,
                detail={
                    "error": f"Semgrep scan failed: {result.stderr}",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            )
        
        # Parse SARIF to count findings
        finding_count = 0
        try:
            with open(output_path, 'r') as f:
                sarif_data = json.load(f)
            finding_count = sum(
                len(run.get('results', [])) 
                for run in sarif_data.get('runs', [])
            )
        except Exception:
            # If we can't parse SARIF, still return success but with 0 findings
            pass
        
        return {
            "status": "success",
            "output_path": str(output_path),
            "finding_count": finding_count,
            "duration_seconds": duration
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Semgrep scan timed out"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', 8082))
    uvicorn.run(app, host='0.0.0.0', port=port)
