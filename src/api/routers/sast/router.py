"""SAST tools router."""

from api.mcp_router import MCPRouter
from api.tools.sast.sast_list_tools import sast_list_tools

router = MCPRouter()

router.tool()(sast_list_tools)
