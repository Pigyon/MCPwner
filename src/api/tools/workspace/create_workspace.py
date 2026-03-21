"""Create workspace tool."""

import logging
import sys

from deps import get_workspace_service

logger = logging.getLogger(__name__)


def create_workspace(source_type: str, source: str) -> dict:
    """
    Create workspace from GitHub repo, local directory, or virtual workspace.

    Args:
        source_type: "github", "local", or "virtual"
        source: For github: a GitHub URL or "owner/repo" shorthand (e.g. "octocat/Hello-World").
                For local: an absolute path that exists inside the container
                (requires a volume mount in docker-compose.yaml).
                For virtual: a descriptive name (e.g. "enumeration-workspace").
                Virtual workspaces are used for enumeration/discovery tools that don't need source code.

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
