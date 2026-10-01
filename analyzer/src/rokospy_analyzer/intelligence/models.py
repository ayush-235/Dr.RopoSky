"""Data models for Project Intelligence, Structural Analysis, and Coverage Telemetry."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class RouteInfo(BaseModel):
    """Information about a discovered API route or endpoint."""
    method: str
    path: str
    file: str
    line: int
    has_validation: bool = False
    has_auth: bool = False
    has_role_check: bool = False
    has_ownership_check: bool = False
    is_sensitive: bool = False
    is_admin: bool = False
    is_payment: bool = False
    handler_name: Optional[str] = None


class ProjectIntelligence(BaseModel):
    """Comprehensive structural intelligence extracted statically from the project."""
    project_type: str = Field(default="general", description="backend_api | frontend_spa | fullstack | library | script | general")
    frameworks: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    routes_detected: List[RouteInfo] = Field(default_factory=list)
    env_vars_used: List[str] = Field(default_factory=list)
    env_vars_documented: List[str] = Field(default_factory=list)
    missing_env_vars: List[str] = Field(default_factory=list)
    direct_dependencies: List[str] = Field(default_factory=list)
    has_lockfile: bool = False
    lockfile_names: List[str] = Field(default_factory=list)
    has_tests: bool = False
    test_frameworks: List[str] = Field(default_factory=list)
    test_files_count: int = 0
    db_orm_detected: List[str] = Field(default_factory=list)
    auth_mechanisms_detected: List[str] = Field(default_factory=list)
    has_global_auth: bool = False
    god_modules: List[str] = Field(default_factory=list)
    scattered_config_files: List[str] = Field(default_factory=list)
    layer_violations: List[str] = Field(default_factory=list)



class PillarCoverage(BaseModel):
    """Analysis coverage details for a specific evaluation pillar."""
    pillar: str
    coverage_pct: int
    verifiable_aspects: List[str] = Field(default_factory=list)
    unverified_aspects: List[str] = Field(default_factory=list)


class AnalysisCoverage(BaseModel):
    """Overall and pillar-by-pillar static analysis coverage telemetry."""
    overall_coverage_pct: int
    pillars: Dict[str, PillarCoverage]
    evaluation_summary: str
