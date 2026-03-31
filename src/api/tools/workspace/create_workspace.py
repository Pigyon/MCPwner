"""Create workspace tool."""

import logging
import sys

from deps import get_workspace_service

logger = logging.getLogger(__name__)


def create_workspace(source_type: str, source: str) -> dict:
    """
    Create workspace from GitHub repo, local directory, or virtual workspace.

    Args:
        source_type: "github", "local", "local_path", or "virtual"
        source: For github: a GitHub URL or "owner/repo" shorthand (e.g. "octocat/Hello-World").
                For local: an absolute path that exists inside the container
                (requires a volume mount in docker-compose.yaml).
                For local_path: an absolute path (or ~/relative) to a local codebase on the host.
                The code is used in-place (not copied). Works with existing git repos.
                Reports are stored separately under the workspace base directory.
                For virtual: a descriptive name (e.g. "reconnaissance-workspace").
                Virtual workspaces are used for reconnaissance tools that don't need source code.

    Returns:
        Dictionary with workspace_id, source_type, source, and created_at
    """
    print(
        f"[MCP SERVER] create_workspace called: type={source_type}, source={source}",
        file=sys.stderr,
    )
    service = get_workspace_service()
    result = service.create_workspace(source_type, source)
    logger.info(f"Workspace created: {result['workspace_id']}")
    return result
