"""Health check endpoint."""

from fastapi import APIRouter
from app.db.supabase_client import supabase_store
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Service liveness probe."""
    mode = "Supabase" if supabase_store.is_live else "Local Fallback"
    return HealthResponse(persistence=mode)
