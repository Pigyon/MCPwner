"""Health tools router."""

from api.mcp_router import MCPRouter
from api.tools.health.health_check import health_check
from api.tools.health.list_tools import list_tools

router = MCPRouter()

router.tool()(list_tools)
router.tool()(health_check)
