"""Reconnaissance tools router."""

from api.mcp_router import MCPRouter
from api.tools.reconnaissance.get_report import get_reconnaissance_report
from api.tools.reconnaissance.list_tools import reconnaissance_list_tools
from api.tools.reconnaissance.scan import run_reconnaissance_scan

router = MCPRouter()

router.tool()(reconnaissance_list_tools)
router.tool()(run_reconnaissance_scan)
router.tool()(get_reconnaissance_report)
