"""Secrets tools router."""

from api.mcp_router import MCPRouter
from api.tools.secrets.get_report import get_secrets_report
from api.tools.secrets.list_tools import secrets_list_tools
from api.tools.secrets.scan import run_secrets_scan

router = MCPRouter()

router.tool()(secrets_list_tools)
router.tool()(run_secrets_scan)
router.tool()(get_secrets_report)
