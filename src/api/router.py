"""Main API router that aggregates all tools."""

from fastmcp import FastMCP

import config.tools as tools_module
from api.mcp_router import MCPRouter
from api.tools.codeql.create_codeql_database import create_codeql_database
from api.tools.codeql.execute_query import execute_query
from api.tools.codeql.list_databases import list_databases
from api.tools.codeql.list_query_packs import list_query_packs
from api.tools.common import create_report_tool, create_scan_tool
from api.tools.dast.list_tools import dast_list_tools
from api.tools.fuzzing.list_tools import fuzzing_list_tools
from api.tools.health.health_check import health_check
from api.tools.health.list_tools import health_list_tools
from api.tools.iac.list_tools import iac_list_tools
from api.tools.reconnaissance.chain import run_reconnaissance_chain
from api.tools.reconnaissance.list_tools import reconnaissance_list_tools
from api.tools.sast.list_tools import sast_list_tools
from api.tools.sca.list_tools import sca_list_tools
from api.tools.secrets.list_tools import secrets_list_tools
from api.tools.utilities.detect_languages import detect_languages
from api.tools.utilities.list_tools import utilities_list_tools
from api.tools.workspace.cleanup_workspace import cleanup_workspace
from api.tools.workspace.create_workspace import create_workspace
from api.tools.workspace.list_workspaces import list_workspaces
from config.tools import tools_for_category

# Standard category configurations: (list_tools_func, extra_tools_list)
CATEGORY_CONFIGS = {
    "sast": (sast_list_tools, []),
    "sca": (sca_list_tools, []),
    "secrets": (secrets_list_tools, []),
    "reconnaissance": (reconnaissance_list_tools, [run_reconnaissance_chain]),
    "utilities": (utilities_list_tools, []),
    "fuzzing": (fuzzing_list_tools, []),
    "dast": (dast_list_tools, []),
    "iac": (iac_list_tools, []),
}


class MainRouter(MCPRouter):
    """
    Main API router that dynamically registers tools based on health at registration time.
    """

    def register_tools(self, mcp: FastMCP):
        # Clear existing tools to support clean re-registries/reloads
        self._tools.clear()

        # 1. Always register core tools
        self.add_tools(
            health_list_tools,
            health_check,
            create_workspace,
            list_workspaces,
            cleanup_workspace,
        )

        # 2. Register detect_languages if linguist service is healthy
        if "linguist" in tools_module.HEALTHY_TOOLS:
            self.add_tools(detect_languages)

        # 3. Register CodeQL tools if CodeQL is healthy
        if "codeql" in tools_module.HEALTHY_TOOLS:
            self.add_tools(
                create_codeql_database,
                list_databases,
                execute_query,
                list_query_packs,
            )

        # 4. Register standard category tools dynamically if they have healthy tools
        for category, (list_func, extra_tools) in CATEGORY_CONFIGS.items():
            if tools_for_category(category):
                self.add_tools(
                    list_func,
                    create_scan_tool(category),
                    create_report_tool(category),
                )
                if extra_tools:
                    self.add_tools(*extra_tools)

        # 5. Call parent implementation to register all built list of tools
        super().register_tools(mcp)


# Create main API router instance
router = MainRouter()
