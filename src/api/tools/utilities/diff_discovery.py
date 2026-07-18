"""Diff-mode discovery: extract changed hunks from a git range for targeted vuln research."""

import re
import subprocess
from pathlib import Path
from typing import Optional

from deps import get_workspace_service


def diff_discovery(
    workspace_id: str,
    git_range: str = "HEAD~1..HEAD",
    file_filter: Optional[str] = None,
) -> dict:
    """Extract changed code hunks from a git commit range as seed material for
    vulnerability research (variant analysis, diff-anchored hypothesis generation).

    Args:
        workspace_id: UUID of the workspace (must be a git repo)
        git_range: Git revision range (e.g. "abc123..def456", "HEAD~5..HEAD", "main..feature")
        file_filter: Optional glob to restrict files (e.g. "*.py", "src/**/*.js")
    """
    try:
        ws_service = get_workspace_service()
        workspace_path = ws_service.repository.get_valid_workspace_path(workspace_id)
        source_dir = Path(workspace_path)

        if not (source_dir / ".git").exists():
            return {"status": "error", "error": "Workspace is not a git repository"}

        cmd = ["git", "diff", "--unified=5", "--stat", git_range, "--"]
        if file_filter:
            cmd.append(file_filter)

        stat_result = subprocess.run(
            cmd, cwd=str(source_dir), capture_output=True, text=True, timeout=30
        )

        diff_cmd = ["git", "diff", "--unified=5", git_range, "--"]
        if file_filter:
            diff_cmd.append(file_filter)

        diff_result = subprocess.run(
            diff_cmd, cwd=str(source_dir), capture_output=True, text=True, timeout=60
        )
        if diff_result.returncode != 0:
            return {"status": "error", "error": diff_result.stderr[:500]}

        hunks = _parse_hunks(diff_result.stdout)

        log_cmd = ["git", "log", "--oneline", "--no-decorate", git_range, "--"]
        log_result = subprocess.run(
            log_cmd, cwd=str(source_dir), capture_output=True, text=True, timeout=10
        )

        files_changed = len({h["file"] for h in hunks if h.get("file")})

        return {
            "status": "success",
            "workspace_id": workspace_id,
            "git_range": git_range,
            "commits": log_result.stdout.strip().splitlines() if log_result.returncode == 0 else [],
            "stat": stat_result.stdout.strip() if stat_result.returncode == 0 else "",
            "files_changed": files_changed,
            "hunks": hunks[:50],
            "discovery_lane": "diff",
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Git diff timed out"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# Matches `diff --git a/<path> b/<path>`, tolerating git's quoting of paths with
# spaces/special chars (which would break a naive ' b/' split).
_DIFF_GIT_RE = re.compile(r'^diff --git "?[ab]/.*?"? "?b/(.+?)"?$')


def _parse_hunks(diff_output: str) -> list:
    """Parse a unified diff into per-hunk entries.

    Files with no ``@@`` hunk (binary/rename/mode-only changes) still get a single
    placeholder entry so a swapped binary or rename isn't invisible to the lane.
    """
    hunks = []
    current_file = None
    current_hunk_lines = []
    current_hunk_header = None
    file_had_hunk = False

    def flush_hunk():
        if current_file and current_hunk_lines:
            hunks.append(
                {
                    "file": current_file,
                    "header": current_hunk_header,
                    "diff": "\n".join(current_hunk_lines[-80:]),
                }
            )

    for line in diff_output.splitlines():
        m = _DIFF_GIT_RE.match(line)
        if m:
            flush_hunk()
            # A file whose diff carried no @@ hunk still deserves a placeholder.
            if current_file and not file_had_hunk:
                hunks.append({"file": current_file, "header": None, "diff": ""})
            current_file = m.group(1)
            current_hunk_lines = []
            current_hunk_header = None
            file_had_hunk = False

        elif line.startswith("@@"):
            flush_hunk()
            file_had_hunk = True
            current_hunk_header = line
            current_hunk_lines = [line]

        elif current_hunk_header:
            current_hunk_lines.append(line)

    flush_hunk()
    if current_file and not file_had_hunk:
        hunks.append({"file": current_file, "header": None, "diff": ""})

    return hunks
