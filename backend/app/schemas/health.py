"""Health endpoint schema."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service health state")
    service: str = Field(default="rokospy-backend", description="Service identifier")
    version: str = Field(default="0.1.0", description="Service API version")
    persistence: str = Field(default="Local Fallback", description="Active persistence backend (Supabase or Local Fallback)")
