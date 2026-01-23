"""CodeQL tools router."""

from fastmcp import MCPRouter
from api.tools.codeql.detect_languages import detect_languages
from api.tools.codeql.create_codeql_database import create_codeql_database
from api.tools.codeql.list_databases import list_databases
from api.tools.codeql.execute_query import execute_query
from api.tools.codeql.list_query_packs import list_query_packs

router = MCPRouter(prefix="codeql")

router.tool()(detect_languages)
router.tool()(create_codeql_database)
router.tool()(list_databases)
router.tool()(execute_query)
router.tool()(list_query_packs)
