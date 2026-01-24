"""HTTP service wrapper for GitHub Linguist."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import json
from pathlib import Path
from typing import Optional

app = FastAPI(title="Linguist Service", version="1.0.0")


# Request/Response Models
class DetectLanguagesRequest(BaseModel):
    path: str


class HealthResponse(BaseModel):
    status: str
    service: str


class VersionResponse(BaseModel):
    version: str
    status: str


@app.get('/health', response_model=HealthResponse)
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "linguist"}


@app.post('/detect')
def detect_languages(request: DetectLanguagesRequest):
    """
    Detect languages in a directory.
    
    Returns language breakdown and statistics.
    """
    try:
        # Validate path exists
        if not Path(request.path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Path does not exist: {request.path}"
            )
        
        # Run linguist
        result = subprocess.run(
            ["github-linguist", "--json", request.path],
            capture_output=True,
            text=True,
            timeout=60,
            check=True
        )
        
        # Parse JSON output
        languages_data = json.loads(result.stdout)
        
        return {
            "status": "success",
            "languages": languages_data
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Linguist detection timed out"
        )
        
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Linguist execution failed: {e.stderr}"
        )
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse linguist output: {str(e)}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/version', response_model=VersionResponse)
def version():
    """Get linguist version."""
    try:
        result = subprocess.run(
            ["github-linguist", "--version"],
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


if __name__ == '__main__':
    import uvicorn
    import os
    port = int(os.getenv('PORT', 8081))
    uvicorn.run(app, host='0.0.0.0', port=port)
