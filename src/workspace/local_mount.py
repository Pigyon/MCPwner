"""
Local Mount Management - Handles local directory mounting for workspaces.

This module provides functionality for validating and tracking local directory
mounts in workspace metadata.
"""

import os
from typing import Any, Dict


class LocalMountError(Exception):
    """Raised when local mount operations fail."""

    pass


def validate_local_path(path: str) -> str:
    """
    Validate local directory path.

    Validates that the path:
    - Is an absolute path
    - Exists on the filesystem
    - Is a directory (not a file)

    Args:
        path: Local directory path to validate

    Returns:
        Absolute path (normalized)

    Raises:
        LocalMountError: If path is invalid, doesn't exist, or is not a directory
    """
    # Check if path is absolute
    if not os.path.isabs(path):
        raise LocalMountError(f"Path must be absolute: {path}")

    # Normalize path
    normalized_path = os.path.abspath(os.path.expanduser(path))

    # Check if path exists
    if not os.path.exists(normalized_path):
        raise LocalMountError(f"Path does not exist: {normalized_path}")

    # Check if path is a directory
    if not os.path.isdir(normalized_path):
        raise LocalMountError(f"Path is not a directory: {normalized_path}")

    return normalized_path


def setup_local_mount(
    local_path: str, workspace_id: str, base_path: str = "/workspaces"
) -> Dict[str, Any]:
    """
    Setup local directory mount for workspace.

    Validates the local path and prepares metadata for mounting.
    The actual Docker volume mount is handled by docker-compose.yaml.

    Args:
        local_path: Absolute path to local directory
        workspace_id: Unique workspace identifier
        base_path: Base directory for workspaces (default: /workspaces)

    Returns:
        Dictionary containing:
            - local_path: Validated absolute path to local directory
            - mount_path: Path where directory will be mounted in container
            - workspace_id: Workspace identifier

    Raises:
        LocalMountError: If local path validation fails
    """
    # Validate local path
    validated_path = validate_local_path(local_path)

    # Determine mount path in container
    mount_path = f"{base_path}/{workspace_id}/source"

    return {
        "local_path": validated_path,
        "mount_path": mount_path,
        "workspace_id": workspace_id,
    }
