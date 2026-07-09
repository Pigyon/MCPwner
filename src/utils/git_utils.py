"""Git utilities for MCPwner services."""

import subprocess
from pathlib import Path
from typing import Optional, Union


def run_git_command(
    args: list[str],
    cwd: Optional[Union[str, Path]] = None,
    timeout: Optional[int] = None,
    env: Optional[dict[str, str]] = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """
    Execute a git command.

    Args:
        args: Git command arguments
        cwd: Working directory for the command
        timeout: Optional timeout in seconds
        env: Optional environment variables
        check: Whether to raise CalledProcessError on non-zero exit

    Returns:
        CompletedProcess instance containing stdout and stderr
    """
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
        env=env,
    )


def init_git(path: Union[str, Path]) -> None:
    """
    Initialize a new git repository in the given path.

    Args:
        path: Directory path to initialize

    Raises:
        RuntimeError: If git init fails
    """
    try:
        run_git_command(["init"], cwd=path)
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
        run_git_command(["config", "user.email", email], cwd=path)
        run_git_command(["config", "user.name", name], cwd=path)
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
        run_git_command(["add", "."], cwd=path)
        run_git_command(["commit", "-m", message], cwd=path)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"Failed to commit files: {error_msg}")
