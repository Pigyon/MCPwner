"""CodeQL tools router."""

from api.mcp_router import MCPRouter
from api.tools.codeql.detect_languages import detect_languages
from api.tools.codeql.create_codeql_database import create_codeql_database
from api.tools.codeql.list_databases import list_databases
from api.tools.codeql.execute_query import execute_query
from api.tools.codeql.list_query_packs import list_query_packs
from api.tools.codeql.extract_code_context import extract_code_context
from api.tools.codeql.get_function_context import get_function_context
from api.tools.codeql.get_callers import get_callers
from api.tools.codeql.get_callees import get_callees
from api.tools.codeql.search_functions import search_functions
from api.tools.codeql.list_functions import list_functions

router = MCPRouter(prefix=None)

router.tool()(detect_languages)
router.tool()(create_codeql_database)
router.tool()(list_databases)
router.tool()(execute_query)
router.tool()(list_query_packs)
router.tool()(extract_code_context)
router.tool()(get_function_context)
router.tool()(get_callers)
router.tool()(get_callees)
router.tool()(search_functions)
router.tool()(list_functions)
