"""Main API router that aggregates all sub-routers."""

from api.mcp_router import MCPRouter
from api.routers.codeql.router import router as codeql_router
from api.routers.health.router import router as health_router
from api.routers.reconnaissance.router import router as reconnaissance_router
from api.routers.sast.router import router as sast_router
from api.routers.sca.router import router as sca_router
from api.routers.secrets.router import router as secrets_router
from api.routers.workspace.router import router as workspace_router

# Create main API router
router = MCPRouter()

# Include all sub-routers
router.include_router(health_router)
router.include_router(workspace_router)
router.include_router(codeql_router)
router.include_router(sast_router)
router.include_router(sca_router)
router.include_router(secrets_router)
router.include_router(reconnaissance_router)
