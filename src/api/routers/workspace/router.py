"""Workspace tools router."""

from fastmcp import MCPRouter
from api.tools.workspace.create_workspace import create_workspace
from api.tools.workspace.list_workspaces import list_workspaces
from api.tools.workspace.cleanup_workspace import cleanup_workspace

router = MCPRouter(prefix="workspace")

router.tool()(create_workspace)
router.tool()(list_workspaces)
router.tool()(cleanup_workspace)
