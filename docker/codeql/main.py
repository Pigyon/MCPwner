"""CodeQL HTTP Service - wraps the CodeQL CLI as a REST API (port 8080)."""

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="CodeQL Service", version="1.0.0")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    custom_query: Optional[str] = None


class HealthResponse(BaseModel):
    status: str


class VersionResponse(BaseModel):
    available: bool
    version: Optional[str] = None
    details: Optional[dict] = None
    error: Optional[str] = None


@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "healthy"}


@app.get("/version", response_model=VersionResponse)
def get_version():
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
    try:
        if not Path(request.source_path).exists():
            raise HTTPException(status_code=400, detail=f"Source path not found: {request.source_path}")

        cmd = [
            "codeql",
            "database",
            "create",
            request.db_path,
            f"--language={request.language}",
            f"--source-root={request.source_path}",
            "--overwrite",
        ]

        lang = request.language.lower()
        interpreted = {"javascript", "typescript", "python", "ruby"}
        # build-mode=none extracts Java/C#/Kotlin without a build (CodeQL >= 2.16).
        build_mode_none = {"java", "csharp", "kotlin"}
        logger.info(f"Checking language: '{request.language}'")

        if lang in interpreted:
            logger.info("Disabling autobuild for interpreted language")
            cmd.append(f"--command={str(Path('/bin/true'))}")
            cmd.append("--no-run-unnecessary-builds")
        elif lang in build_mode_none:
            logger.info(f"Using --build-mode=none for '{lang}' (no build/JDK needed)")
            cmd.append("--build-mode=none")
        else:
            logger.info(f"Language '{lang}' uses the default autobuilder (needs build tools)")

        logger.info(f"Creating database: {' '.join(cmd)}")

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

        return {
            "database_id": f"{request.workspace_id}-{request.language}",
            "language": request.language,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
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
    try:
        result = subprocess.run(
            ["codeql", "resolve", "queries", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return {
                "packs": ["security-extended", "security-and-quality"],
                "raw_output": result.stdout,
            }
        raise HTTPException(status_code=500, detail=result.stderr)

    except Exception as e:
        logger.error(f"Query pack listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _detect_db_language(database_path: str) -> Optional[str]:
    meta = Path(database_path) / "codeql-database.yml"
    if not meta.exists():
        return None
    try:
        data = yaml.safe_load(meta.read_text())
        return data.get("primaryLanguage") or data.get("languages", [None])[0]
    except Exception as e:
        logger.warning(f"Could not read database language: {e}")
        return None


def _build_adhoc_qlpack(custom_query: str, language: str) -> str:
    """Write the custom query into a temp qlpack that depends on the language's
    standard library so its imports resolve. Returns the pack dir (caller cleans up)."""
    # `database analyze` only emits SARIF for queries carrying result-set metadata;
    # fail fast with a clear message instead of a mysterious empty 0-finding run.
    if not re.search(r"@kind\s+(problem|path-problem)", custom_query) or "@id" not in custom_query:
        raise HTTPException(
            status_code=400,
            detail="Custom query must include '@kind problem' (or 'path-problem') and an '@id' "
            "metadata comment so CodeQL can emit SARIF.",
        )

    pack_dir = tempfile.mkdtemp(prefix="mcpwner_adhoc_", dir="/tmp")
    try:
        qlpack = {
            "name": "mcpwner/adhoc-query",
            "version": "0.0.1",
            "dependencies": {f"codeql/{language}-all": "*"},
        }
        (Path(pack_dir) / "qlpack.yml").write_text(yaml.safe_dump(qlpack))
        (Path(pack_dir) / "custom.ql").write_text(custom_query)

        install = subprocess.run(
            ["codeql", "pack", "install", pack_dir],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if install.returncode != 0:
            logger.warning(f"codeql pack install non-zero (continuing): {install.stderr[:300]}")
        return pack_dir
    except Exception:
        shutil.rmtree(pack_dir, ignore_errors=True)
        raise


@app.post("/query/execute")
def execute_query(request: ExecuteQueryRequest):
    adhoc_pack_dir: Optional[str] = None
    try:
        if not Path(request.database_path).exists():
            raise HTTPException(status_code=400, detail=f"Database not found: {request.database_path}")

        if request.custom_query:
            language = _detect_db_language(request.database_path)
            if not language:
                raise HTTPException(
                    status_code=400,
                    detail="Could not determine database language for custom query.",
                )
            logger.info(f"Building ad-hoc qlpack for custom {language} query")
            adhoc_pack_dir = _build_adhoc_qlpack(request.custom_query, language)
            query_spec = str(Path(adhoc_pack_dir) / "custom.ql")
        elif request.query_pack.endswith(".qls"):
            query_spec = request.query_pack
        else:
            query_spec = f"codeql/{request.query_pack}"

        # CodeQL default heap (~769 MiB) OOMs on real databases; tune via env vars.
        ram_mb = os.environ.get("CODEQL_RAM_MB", "4096")
        threads = os.environ.get("CODEQL_THREADS", "0")  # 0 = one per core

        cmd = [
            "codeql",
            "database",
            "analyze",
            request.database_path,
            query_spec,
            "--format=sarif-latest",
            f"--output={request.output_path}",
            "--sarif-add-snippets",
            f"--ram={ram_mb}",
            f"--threads={threads}",
        ]

        if request.query_name:
            cmd.append(f"--query={request.query_name}")

        logger.info(f"Executing query: {' '.join(cmd)}")

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
    finally:
        # Ad-hoc qlpacks accumulate one dir per custom query on the /tmp tmpfs.
        if adhoc_pack_dir:
            shutil.rmtree(adhoc_pack_dir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
