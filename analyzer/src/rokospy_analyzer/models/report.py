"""Analysis Report models for output serialization."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from rokospy_analyzer.models.finding import NormalizedFinding
from rokospy_analyzer.ai.models import AIExecutionSummary
from rokospy_analyzer.scoring.models import ProjectScore
from rokospy_analyzer.intelligence.models import ProjectIntelligence, AnalysisCoverage


class ScannerStatusEnum(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"


class ScannerExecutionResult(BaseModel):
    scanner: str
    status: ScannerStatusEnum
    findings_count: int = 0
    duration_ms: int = 0
    error_message: Optional[str] = None

    model_config = {
        "use_enum_values": True,
    }


class ProjectMetadata(BaseModel):
    name: str
    source_type: str
    languages: List[str]
    manifests: List[str]
    target_url: Optional[str] = None


class AnalysisExecutionInfo(BaseModel):
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: int = 0
    files_analyzed: int = 0


class SeveritySummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class CategorySummary(BaseModel):
    bug: int = 0
    security: int = 0
    performance: int = 0
    quality: int = 0
    missing_essential: int = 0
    architecture: int = 0


class AnalysisReport(BaseModel):
    schema_version: str = Field(default="1.0", description="Rokospy report schema specification version")
    project: ProjectMetadata
    analysis: AnalysisExecutionInfo
    scanners: List[ScannerExecutionResult]
    findings: List[NormalizedFinding]
    summary: SeveritySummary
    category_summary: CategorySummary
    ai_summary: Optional[AIExecutionSummary] = None
    score: Optional[ProjectScore] = Field(default=None, description="Deterministic 6-pillar and overall project score")
    coverage: Optional[AnalysisCoverage] = Field(default=None, description="Static analysis coverage telemetry across 6 pillars")
    intelligence: Optional[ProjectIntelligence] = Field(default=None, description="Static project intelligence and structure metrics")

    project_id: Optional[str] = None
    scan_id: Optional[str] = None

    model_config = {
        "use_enum_values": True,
    }

