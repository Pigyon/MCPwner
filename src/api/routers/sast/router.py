"""SAST tools router."""

from api.mcp_router import MCPRouter
from api.tools.sast.sast_bandit_get_report import sast_bandit_get_report
from api.tools.sast.sast_bandit_scan import sast_bandit_scan
from api.tools.sast.sast_list_tools import sast_list_tools
from api.tools.sast.sast_semgrep_get_report import sast_semgrep_get_report
from api.tools.sast.sast_semgrep_scan import sast_semgrep_scan

router = MCPRouter()

router.tool()(sast_list_tools)
router.tool()(sast_semgrep_scan)
router.tool()(sast_semgrep_get_report)
router.tool()(sast_bandit_scan)
router.tool()(sast_bandit_get_report)
