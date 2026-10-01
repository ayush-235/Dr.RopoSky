"""Standardized API Error schemas."""

from pydantic import BaseModel, Field


class APIErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error classification code")
    message: str = Field(..., description="Human-readable sanitized error description")


class APIErrorResponse(BaseModel):
    error: APIErrorDetail
