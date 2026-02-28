"""SAST tools router."""

from api.mcp_router import MCPRouter
from api.tools.sast.get_report import get_sast_report
from api.tools.sast.sast_list_tools import sast_list_tools
from api.tools.sast.scan import run_sast_scan

router = MCPRouter()

router.tool()(sast_list_tools)
router.tool()(run_sast_scan)
router.tool()(get_sast_report)
