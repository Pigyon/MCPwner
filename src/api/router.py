import config.tools as tools_module
from api.mcp_router import MCPRouter
from api.routers.codeql.router import router as codeql_router
from api.routers.dast.router import router as dast_router
from api.routers.fuzzing.router import router as fuzzing_router
from api.routers.health.router import router as health_router
from api.routers.iac.router import router as iac_router
from api.routers.reconnaissance.router import router as reconnaissance_router
from api.routers.sast.router import router as sast_router
from api.routers.sca.router import router as sca_router
from api.routers.secrets.router import router as secrets_router
from api.routers.utilities.router import router as utilities_router
from api.routers.workspace.router import router as workspace_router
from config.tools import tools_for_category

"""Main API router that aggregates all sub-routers."""


# Create main API router
router = MCPRouter()

# Always include core routers
router.include_router(health_router)
router.include_router(workspace_router)


# Conditionally include tool routers
if "codeql" in tools_module.HEALTHY_TOOLS:
    router.include_router(codeql_router)
if tools_for_category("sast"):
    router.include_router(sast_router)
if tools_for_category("sca"):
    router.include_router(sca_router)
if tools_for_category("secrets"):
    router.include_router(secrets_router)
if tools_for_category("reconnaissance"):
    router.include_router(reconnaissance_router)
if "linguist" in tools_module.HEALTHY_TOOLS or tools_for_category("utilities"):
    router.include_router(utilities_router)
if tools_for_category("iac"):
    router.include_router(iac_router)
if tools_for_category("fuzzing"):
    router.include_router(fuzzing_router)
if tools_for_category("dast"):
    router.include_router(dast_router)
