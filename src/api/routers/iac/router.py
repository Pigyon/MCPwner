"""Infrastructure-as-Code (IaC) tools router."""

from api.mcp_router import MCPRouter
from api.tools.iac.get_report import get_iac_report
from api.tools.iac.list_tools import iac_list_tools
from api.tools.iac.scan import run_iac_scan

router = MCPRouter()

router.tool()(iac_list_tools)
router.tool()(run_iac_scan)
router.tool()(get_iac_report)
