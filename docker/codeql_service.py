"""
CodeQL HTTP Service - Infrastructure Component

This FastAPI service runs INSIDE the codeql-executor container as a separate microservice.
It provides a REST API for CodeQL operations (database creation, query execution).

Architecture:
- Location: docker/codeql_service.py (infrastructure, not business logic)
- Container: codeql-executor (separate from mcpwner-server)
- Communication: HTTP API on port 8080
- Called by: src/clients/codeql.py (CodeQLClient)

This is NOT part of the MCP server's service layer (src/services/).
It's a standalone HTTP service that wraps CodeQL CLI operations.
"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="CodeQL Service", version="1.0.0")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request/Response Models
class CreateDatabaseRequest(BaseModel):
    workspace_id: str
    language: str
    source_path: str
    db_path: str


class ExecuteQueryRequest(BaseModel):
    database_path: str
    query_pack: str
    output_path: str
    query_name: Optional[str] = None


class HealthResponse(BaseModel):
    status: str


class VersionResponse(BaseModel):
    available: bool
    version: Optional[str] = None
    details: Optional[dict] = None
    error: Optional[str] = None


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/version", response_model=VersionResponse)
def get_version():
    """Get CodeQL version."""
    try:
        result = subprocess.run(
            ["codeql", "version", "--format=json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            version_data = json.loads(result.stdout)
            return {
                "available": True,
                "version": version_data.get("version", "unknown"),
                "details": version_data,
            }
        return {"available": False, "error": result.stderr}
    except Exception as e:
        logger.error(f"Version check failed: {e}")
        return {"available": False, "error": str(e)}


@app.post("/database/create")
def create_database(request: CreateDatabaseRequest):
    """Create a CodeQL database."""
    try:
        # Validate source path exists
        if not Path(request.source_path).exists():
            raise HTTPException(status_code=400, detail=f"Source path not found: {request.source_path}")

        # Build CodeQL command
        cmd = [
            "codeql",
            "database",
            "create",
            request.db_path,
            f"--language={request.language}",
            f"--source-root={request.source_path}",
            "--overwrite",
        ]

        # For interpreted languages (javascript, typescript, python, ruby), disable autobuild
        # to avoid build failures in environments without build tools (npm, pip, etc.)
        logger.info(f"Checking language: '{request.language}'")

        if request.language.lower() in ["javascript", "typescript", "python", "ruby"]:
            logger.info("Disabling autobuild for interpreted language")
            cmd.append(f"--command={str(Path('/bin/true'))}")
            cmd.append("--no-run-unnecessary-builds")
        else:
            logger.info(f"Language '{request.language}' not in interpreted list")

        # Add verbosity to debug autobuild failures
        # cmd.append("-v")

        logger.info(f"Creating database: {' '.join(cmd)}")

        # Execute CodeQL command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Database creation failed: {result.stderr}")
            logger.error(f"STDOUT: {result.stdout}")
            raise HTTPException(
                status_code=500,
                detail={"error": "Database creation failed", "details": result.stderr},
            )

        # Return success response
        return {
            "database_id": f"{request.workspace_id}-{request.language}",
            "language": request.language,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "path": request.db_path,
            "stdout": result.stdout,
        }

    except subprocess.TimeoutExpired:
        logger.error("Database creation timed out")
        raise HTTPException(status_code=500, detail="Database creation timed out after 10 minutes")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/query/packs")
def list_query_packs():
    """List available CodeQL query packs."""
    try:
        # Get available query packs
        result = subprocess.run(
            ["codeql", "resolve", "queries", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            # Parse and return query packs
            return {
                "packs": ["security-extended", "security-and-quality"],
                "raw_output": result.stdout,
            }
        raise HTTPException(status_code=500, detail=result.stderr)

    except Exception as e:
        logger.error(f"Query pack listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/execute")
def execute_query(request: ExecuteQueryRequest):
    """Execute a CodeQL query."""
    try:
        # Validate database exists
        if not Path(request.database_path).exists():
            raise HTTPException(status_code=400, detail=f"Database not found: {request.database_path}")

        # Determine query specifier (pack or suite)
        if request.query_pack.endswith(".qls"):
            query_spec = request.query_pack
        else:
            query_spec = f"codeql/{request.query_pack}"

        # Build CodeQL command
        cmd = [
            "codeql",
            "database",
            "analyze",
            request.database_path,
            query_spec,
            "--format=sarif-latest",
            f"--output={request.output_path}",
            "--sarif-add-snippets",
        ]

        if request.query_name:
            cmd.append(f"--query={request.query_name}")

        logger.info(f"Executing query: {' '.join(cmd)}")

        # Execute CodeQL command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"Query execution failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail={"error": "Query execution failed", "details": result.stderr},
            )

        # Return success response
        return {
            "status": "success",
            "output_path": request.output_path,
            "stdout": result.stdout,
        }

    except subprocess.TimeoutExpired:
        logger.error("Query execution timed out")
        raise HTTPException(status_code=500, detail="Query execution timed out after 10 minutes")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
