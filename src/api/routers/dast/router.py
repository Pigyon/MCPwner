"""DAST tools router."""

from api.mcp_router import MCPRouter
from api.tools.dast.get_report import get_dast_report
from api.tools.dast.list_tools import dast_list_tools
from api.tools.dast.scan import run_dast_scan

router = MCPRouter()

router.tool()(dast_list_tools)
router.tool()(run_dast_scan)
router.tool()(get_dast_report)
