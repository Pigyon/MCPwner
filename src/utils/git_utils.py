"""Git utilities for MCPwner services."""

import subprocess
from pathlib import Path
from typing import Union


def init_git(path: Union[str, Path]) -> None:
    """
    Initialize a new git repository in the given path.

    Args:
        path: Directory path to initialize

    Raises:
        RuntimeError: If git init fails
    """
    try:
        subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"Failed to run git init: {error_msg}")


def config_git(path: Union[str, Path], email: str = "mcpwner@local", name: str = "MCPwner") -> None:
    """
    Configure user email and name for the git repository.

    Args:
        path: Directory path of the git repo
        email: User email to configure
        name: User name to configure

    Raises:
        RuntimeError: If git config fails
    """
    try:
        subprocess.run(
            ["git", "config", "user.email", email], cwd=path, check=True, capture_output=True, text=True
        )
        subprocess.run(
            ["git", "config", "user.name", name], cwd=path, check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"Failed to configure git: {error_msg}")


def commit_git(path: Union[str, Path], message: str = "Initial commit for analysis") -> None:
    """
    Add all files and commit them to the git repository.

    Args:
        path: Directory path of the git repo
        message: Commit message

    Raises:
        RuntimeError: If git add or commit fails
    """
    try:
        subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "commit", "-m", message], cwd=path, check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"Failed to commit files: {error_msg}")


def ensure_git_repo(path: Union[str, Path]) -> None:
    """
    Ensure the given path is a git repository.
    If not, initialize it, configure it, and commit all files.

    Args:
        path: Directory path to check/initialize

    Raises:
        RuntimeError: If any git operation fails
    """
    path = Path(path)
    if (path / ".git").exists():
        return

    init_git(path)
    config_git(path)
    commit_git(path)
