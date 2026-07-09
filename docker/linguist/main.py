"""HTTP service wrapper for GitHub Linguist."""

import json
import logging
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from git_utils import commit_git, config_git, init_git
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="Linguist Service", version="1.0.0")


class DetectLanguagesRequest(BaseModel):
    path: str


class HealthResponse(BaseModel):
    status: str
    service: str


class VersionResponse(BaseModel):
    version: str
    status: str


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "linguist"}


@app.post("/detect")
def detect_languages(request: DetectLanguagesRequest):
    """
    Detect languages in a directory.

    Returns language breakdown and statistics.
    """
    try:
        if not Path(request.path).exists():
            raise HTTPException(status_code=404, detail=f"Path does not exist: {request.path}")

        # Linguist requires a git repo; init one if missing.
        try:
            if not (Path(request.path) / ".git").exists():
                init_git(request.path)
                config_git(request.path, email="mcpwner@local", name="MCPwner")
                commit_git(request.path, message="Initial commit")
        except RuntimeError as e:
            # Non-fatal: linguist may still work or fail with a clearer error later.
            logger.warning(f"Failed to initialize git repo: {e}")

        result = subprocess.run(
            ["github-linguist", "--json", request.path],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )

        languages_data = json.loads(result.stdout)

        return {"status": "success", "languages": languages_data}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Linguist detection timed out")

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Linguist execution failed: {e.stderr}")

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse linguist output: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/version", response_model=VersionResponse)
def version():
    """Get linguist version."""
    try:
        result = subprocess.run(
            ["github-linguist", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )

        return {"version": result.stdout.strip(), "status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.getenv("PORT", 8081))
    uvicorn.run(app, host="0.0.0.0", port=port)
