"""Source-fuzzing tools router."""

from api.mcp_router import MCPRouter
from api.tools.fuzzing.get_report import get_fuzzing_report
from api.tools.fuzzing.list_tools import fuzzing_list_tools
from api.tools.fuzzing.scan import run_fuzzing_scan

router = MCPRouter()

router.tool()(fuzzing_list_tools)
router.tool()(run_fuzzing_scan)
router.tool()(get_fuzzing_report)
