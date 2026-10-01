"""API v1 router assembly."""

from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.comparison import router as comparison_router
from app.api.routes.projects import router as projects_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(analysis_router)
api_v1_router.include_router(comparison_router)
api_v1_router.include_router(projects_router)

