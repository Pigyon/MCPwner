"""
CodeQL HTTP service that runs inside the codeql-executor container.
Provides REST API for CodeQL operations.
"""

from flask import Flask, request, jsonify
import subprocess
import json
from pathlib import Path
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route('/version', methods=['GET'])
def get_version():
    """Get CodeQL version."""
    try:
        result = subprocess.run(
            ["codeql", "version", "--format=json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version_data = json.loads(result.stdout)
            return jsonify({
                "available": True,
                "version": version_data.get("version", "unknown"),
                "details": version_data
            }), 200
        else:
            return jsonify({
                "available": False,
                "error": result.stderr
            }), 500
    except Exception as e:
        logger.error(f"Version check failed: {e}")
        return jsonify({
            "available": False,
            "error": str(e)
        }), 500


@app.route('/database/create', methods=['POST'])
def create_database():
    """
    Create a CodeQL database.
    
    Expected JSON body:
    {
        "workspace_id": "uuid",
        "language": "python",
        "source_path": "/workspaces/uuid/source",
        "db_path": "/workspaces/uuid/databases/python"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ["workspace_id", "language", "source_path", "db_path"]
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        workspace_id = data["workspace_id"]
        language = data["language"]
        source_path = data["source_path"]
        db_path = data["db_path"]
        
        # Validate source path exists
        if not Path(source_path).exists():
            return jsonify({"error": f"Source path not found: {source_path}"}), 400
        
        # Build CodeQL command
        cmd = [
            "codeql", "database", "create",
            db_path,
            f"--language={language}",
            f"--source-root={source_path}",
            "--overwrite"
        ]
        
        logger.info(f"Creating database: {' '.join(cmd)}")
        
        # Execute CodeQL command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Database creation failed: {result.stderr}")
            return jsonify({
                "error": "Database creation failed",
                "details": result.stderr
            }), 500
        
        # Return success response
        return jsonify({
            "database_id": f"{workspace_id}-{language}",
            "language": language,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "path": db_path,
            "stdout": result.stdout
        }), 200
        
    except subprocess.TimeoutExpired:
        logger.error("Database creation timed out")
        return jsonify({"error": "Database creation timed out after 10 minutes"}), 500
    except Exception as e:
        logger.error(f"Database creation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/query/packs', methods=['GET'])
def list_query_packs():
    """List available CodeQL query packs."""
    try:
        # Get available query packs
        result = subprocess.run(
            ["codeql", "resolve", "queries", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Parse and return query packs
            # This is a simplified version - actual implementation may need more parsing
            return jsonify({
                "packs": ["security-extended", "security-and-quality"],
                "raw_output": result.stdout
            }), 200
        else:
            return jsonify({"error": result.stderr}), 500
            
    except Exception as e:
        logger.error(f"Query pack listing failed: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Run on all interfaces so it's accessible from other containers
    app.run(host='0.0.0.0', port=8080, debug=False)
