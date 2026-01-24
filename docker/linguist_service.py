"""HTTP service wrapper for GitHub Linguist."""

from flask import Flask, request, jsonify
import subprocess
import json
import os
from pathlib import Path

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "linguist"})


@app.route('/detect', methods=['POST'])
def detect_languages():
    """
    Detect languages in a directory.
    
    Request JSON:
    {
        "path": "/workspaces/workspace-id/source"
    }
    
    Response JSON:
    {
        "languages": {...},
        "status": "success"
    }
    """
    try:
        data = request.get_json()
        workspace_path = data.get('path')
        
        if not workspace_path:
            return jsonify({
                "status": "error",
                "error": "Missing 'path' parameter"
            }), 400
        
        # Validate path exists
        if not Path(workspace_path).exists():
            return jsonify({
                "status": "error",
                "error": f"Path does not exist: {workspace_path}"
            }), 404
        
        # Run linguist
        result = subprocess.run(
            ["github-linguist", "--json", workspace_path],
            capture_output=True,
            text=True,
            timeout=60,
            check=True
        )
        
        # Parse JSON output
        languages_data = json.loads(result.stdout)
        
        return jsonify({
            "status": "success",
            "languages": languages_data
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "error",
            "error": "Linguist detection timed out"
        }), 504
        
    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error",
            "error": f"Linguist execution failed: {e.stderr}"
        }), 500
        
    except json.JSONDecodeError as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to parse linguist output: {str(e)}"
        }), 500
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/version', methods=['GET'])
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
        
        return jsonify({
            "version": result.stdout.strip(),
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8081))
    app.run(host='0.0.0.0', port=port, debug=False)
