"""Data models for deterministic scoring calculations and category breakdowns."""

from typing import Dict
from pydantic import BaseModel, Field


class CategoryScore(BaseModel):
    """Deterministic score for an individual engineering pillar."""
    category: str = Field(..., description="Scoring pillar name")
    score: int = Field(..., ge=0, le=100, description="Score clamped to 0-100")
    finding_count: int = Field(default=0, ge=0, description="Total findings affecting this category")
    deductions: int = Field(default=0, ge=0, description="Total penalty points deducted")
    explanation: str = Field(default="", description="Deterministic explanation of deductions")


class ProjectScore(BaseModel):
    """Deterministic overall project health score and 6-pillar breakdown."""
    overall: int = Field(..., ge=0, le=100, description="Overall weighted score 0-100")
    rating_band: str = Field(..., description="Qualitative rating bracket")
    security: int = Field(..., ge=0, le=100)
    reliability: int = Field(..., ge=0, le=100)
    code_quality: int = Field(..., ge=0, le=100)
    performance: int = Field(..., ge=0, le=100)
    architecture: int = Field(..., ge=0, le=100)
    completeness: int = Field(..., ge=0, le=100)
    categories: Dict[str, CategoryScore] = Field(default_factory=dict)
