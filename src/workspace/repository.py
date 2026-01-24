"""
Repository Management - Handles GitHub repository cloning operations.

This module provides functionality for cloning GitHub repositories with
validation, timeout handling, and error management.
"""

import re
import signal
from pathlib import Path

from git import GitCommandError, Repo


class RepositoryError(Exception):
    """Raised when repository operations fail."""

    pass


class TimeoutError(RepositoryError):
    """Raised when clone operation times out."""

    pass


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
    # Remove trailing .git if present
    source = source.rstrip("/")
    if source.endswith(".git"):
        source = source[:-4]

    # Pattern 1: https://github.com/owner/repo
    if source.startswith("https://github.com/"):
        match = re.match(r"^https://github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)$", source)
        if match:
            return source

    # Pattern 2: github.com/owner/repo
    elif source.startswith("github.com/"):
        match = re.match(r"^github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)$", source)
        if match:
            return f"https://{source}"

    # Pattern 3: owner/repo
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
        TimeoutError: If clone operation exceeds timeout
    """
    # Validate and normalize URL
    validated_url = validate_github_url(github_url)

    # Create target directory
    target_path = Path(base_path) / workspace_id / "source"
    target_path.mkdir(parents=True, exist_ok=True)

    # Set up timeout handler
    def timeout_handler(_signum, _frame):
        raise TimeoutError(f"Clone operation exceeded {timeout} seconds timeout")

    # Clone with timeout
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        Repo.clone_from(validated_url, str(target_path), depth=1, single_branch=True)
        signal.alarm(0)  # Cancel alarm
        return str(target_path.absolute())

    except TimeoutError:
        signal.alarm(0)
        # Clean up partial clone
        if target_path.exists():
            import shutil

            shutil.rmtree(target_path, ignore_errors=True)
        raise

    except GitCommandError as e:
        signal.alarm(0)
        # Clean up partial clone
        if target_path.exists():
            import shutil

            shutil.rmtree(target_path, ignore_errors=True)

        # Parse error message for specific issues
        error_msg = str(e).lower()
        if "not found" in error_msg or "404" in error_msg:
            raise RepositoryError(f"Repository not found: {validated_url}")
        if "network" in error_msg or "connection" in error_msg or "timeout" in error_msg:
            raise RepositoryError(f"Network error while cloning: {validated_url}")
        raise RepositoryError(f"Failed to clone repository: {e}")

    except Exception as e:
        signal.alarm(0)
        # Clean up partial clone
        if target_path.exists():
            import shutil

            shutil.rmtree(target_path, ignore_errors=True)
        raise RepositoryError(f"Unexpected error during clone: {e}")

    finally:
        signal.signal(signal.SIGALRM, old_handler)
