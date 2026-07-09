"""
Repository Management - Handles GitHub repository cloning operations.

This module provides functionality for cloning GitHub repositories with
validation, timeout handling, and error management.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

from utils.git_utils import run_git_command


class RepositoryError(Exception):
    """Raised when repository operations fail."""

    pass


class CloneTimeoutError(RepositoryError):
    """Raised when a clone operation exceeds its timeout."""

    pass


def _cleanup_partial_clone(target_path: Path) -> None:
    """Remove a partially-cloned directory, ignoring errors."""
    if target_path.exists():
        shutil.rmtree(target_path, ignore_errors=True)


def validate_github_url(source: str) -> str:
    """
    Validate and normalize GitHub repository URL.

    Accepts multiple formats:
    - https://github.com/owner/repo
    - github.com/owner/repo
    - owner/repo

    Args:
        source: GitHub repository identifier in various formats

    Returns:
        Normalized HTTPS GitHub URL

    Raises:
        RepositoryError: If URL format is invalid
    """
    source = source.rstrip("/")
    if source.endswith(".git"):
        source = source[:-4]

    if source.startswith("https://github.com/"):
        match = re.match(r"^https://github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)$", source)
        if match:
            return source

    elif source.startswith("github.com/"):
        match = re.match(r"^github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)$", source)
        if match:
            return f"https://{source}"

    else:
        match = re.match(r"^([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)$", source)
        if match:
            return f"https://github.com/{source}"

    raise RepositoryError(f"Invalid GitHub repository format: {source}")


def clone_repository(
    github_url: str,
    workspace_id: str,
    base_path: str = "/workspaces",
    timeout: int = 300,
) -> str:
    """
    Clone a GitHub repository with shallow clone and timeout.

    Performs a shallow clone (depth=1) to minimize disk usage and clone time.
    Includes timeout protection and comprehensive error handling.

    Args:
        github_url: GitHub repository URL (will be validated)
        workspace_id: Unique workspace identifier
        base_path: Base directory for workspaces (default: /workspaces)
        timeout: Maximum seconds for clone operation (default: 300 = 5 minutes)

    Returns:
        Absolute path to cloned repository

    Raises:
        RepositoryError: If clone fails (network, not found, invalid URL)
        CloneTimeoutError: If clone operation exceeds timeout
    """
    validated_url = validate_github_url(github_url)

    target_path = Path(base_path) / workspace_id / "source"
    target_path.mkdir(parents=True, exist_ok=True)

    # Shallow clone via a subprocess with a hard timeout. subprocess.run(timeout=)
    # is thread-safe, unlike signal.alarm — MCP tool calls run on a worker thread,
    # where signal-based timeouts raise "signal only works in main thread".
    try:
        run_git_command(
            ["clone", "--depth", "1", "--single-branch", validated_url, str(target_path)],
            timeout=timeout,
            # Never prompt for credentials: a missing/private repo should fail fast
            # with "repository not found" rather than hang or return an opaque auth error.
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        return str(target_path.absolute())

    except subprocess.TimeoutExpired:
        _cleanup_partial_clone(target_path)
        raise CloneTimeoutError(f"Clone operation exceeded {timeout} seconds timeout")

    except subprocess.CalledProcessError as e:
        _cleanup_partial_clone(target_path)
        error_msg = (e.stderr or "").lower()
        # GitHub returns 404 for missing *or* private repos and then asks for
        # credentials; with prompts disabled git reports a username/auth error.
        if (
            "not found" in error_msg
            or "404" in error_msg
            or "repository not found" in error_msg
            or "could not read username" in error_msg
            or "authentication failed" in error_msg
            or "terminal prompts disabled" in error_msg
        ):
            raise RepositoryError(
                f"Repository not found or is private (no credentials configured): {validated_url}"
            )
        if (
            "could not resolve" in error_msg
            or "network" in error_msg
            or "connection" in error_msg
            or "timed out" in error_msg
        ):
            raise RepositoryError(f"Network error while cloning: {validated_url}")
        raise RepositoryError(f"Failed to clone repository: {e.stderr.strip() or e}")

    except Exception as e:
        _cleanup_partial_clone(target_path)
        raise RepositoryError(f"Unexpected error during clone: {e}")
