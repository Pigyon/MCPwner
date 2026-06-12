"""Utilities tools router."""

from api.mcp_router import MCPRouter
from api.tools.utilities.detect_languages import detect_languages
from api.tools.utilities.get_report import get_utilities_report
from api.tools.utilities.list_tools import utilities_list_tools
from api.tools.utilities.scan import run_utilities_scan

router = MCPRouter()

router.tool()(utilities_list_tools)
router.tool()(detect_languages)
router.tool()(run_utilities_scan)
router.tool()(get_utilities_report)
