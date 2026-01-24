"""HTTP service wrapper for Semgrep SAST tool."""

from flask import Flask, request, jsonify
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "semgrep"})


@app.route('/version', methods=['GET'])
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
        
        return jsonify({
            "version": result.stdout.strip(),
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/scan', methods=['POST'])
def scan():
    """
    Execute Semgrep scan on a workspace.
    
    Request JSON:
    {
        "workspace_path": "/workspaces/{workspace_id}/source",
        "scan_path": "optional/relative/path",  # Optional
        "config": {                              # Optional
            "rules": ["p/security-audit"],
            "exclude": ["tests/"]
        }
    }
    
    Response JSON:
    {
        "status": "success",
        "output_path": "/workspaces/{workspace_id}/reports/sast/semgrep/{timestamp}.sarif",
        "finding_count": 42,
        "duration_seconds": 12.5
    }
    """
    try:
        data = request.get_json()
        workspace_path = data.get('workspace_path')
        scan_path = data.get('scan_path', '.')
        config = data.get('config', {})
        
        if not workspace_path:
            return jsonify({
                "status": "error",
                "error": "Missing 'workspace_path' parameter"
            }), 400
        
        # Build full scan path
        full_scan_path = Path(workspace_path) / scan_path
        
        if not full_scan_path.exists():
            return jsonify({
                "status": "error",
                "error": f"Scan path does not exist: {full_scan_path}"
            }), 404
        
        # Create output directory
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S-%f')[:-3] + 'Z'
        workspace_base = Path(workspace_path).parent
        output_dir = workspace_base / 'reports' / 'sast' / 'semgrep'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f'{timestamp}.sarif'
        
        # Build semgrep command
        cmd = ['semgrep', 'scan', '--sarif', '--output', str(output_path)]
        
        # Add config options
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
            return jsonify({
                "status": "error",
                "error": f"Semgrep scan failed: {result.stderr}",
                "stdout": result.stdout,
                "stderr": result.stderr
            }), 500
        
        # Parse SARIF to count findings
        finding_count = 0
        try:
            with open(output_path, 'r') as f:
                sarif_data = json.load(f)
            finding_count = sum(
                len(run.get('results', [])) 
                for run in sarif_data.get('runs', [])
            )
        except Exception as e:
            # If we can't parse SARIF, still return success but with 0 findings
            pass
        
        return jsonify({
            "status": "success",
            "output_path": str(output_path),
            "finding_count": finding_count,
            "duration_seconds": duration
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "error",
            "error": "Semgrep scan timed out"
        }), 504
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8082))
    app.run(host='0.0.0.0', port=port, debug=False)
