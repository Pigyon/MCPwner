"""SCA tools router."""

from api.mcp_router import MCPRouter
from api.tools.sca.get_report import get_sca_report
from api.tools.sca.sca_list_tools import sca_list_tools
from api.tools.sca.scan import run_sca_scan

router = MCPRouter()

router.tool()(sca_list_tools)
router.tool()(run_sca_scan)
router.tool()(get_sca_report)
