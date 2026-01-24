"""Main API router that aggregates all sub-routers."""

from api.mcp_router import MCPRouter
from api.routers.health.router import router as health_router
from api.routers.workspace.router import router as workspace_router
from api.routers.codeql.router import router as codeql_router
from api.routers.sast.router import router as sast_router

# Create main API router
router = MCPRouter()

# Include all sub-routers
router.include_router(health_router)
router.include_router(workspace_router)
router.include_router(codeql_router)
router.include_router(sast_router)
