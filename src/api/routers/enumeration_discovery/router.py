"""Enumeration & Discovery tools router."""

from api.mcp_router import MCPRouter
from api.tools.enumeration_discovery.get_report import get_enumeration_discovery_report
from api.tools.enumeration_discovery.list_tools import enumeration_discovery_list_tools
from api.tools.enumeration_discovery.scan import run_enumeration_discovery_scan

router = MCPRouter()

router.tool()(enumeration_discovery_list_tools)
router.tool()(run_enumeration_discovery_scan)
router.tool()(get_enumeration_discovery_report)
