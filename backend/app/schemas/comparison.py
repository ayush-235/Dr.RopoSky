"""Comparison models and schemas for Phase 7 Re-scan & Progress Tracking."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from rokospy_analyzer.models.finding import NormalizedFinding
from rokospy_analyzer.models.report import AnalysisReport


class FindingChangeStatus(str, Enum):
    FIXED = "fixed"
    NEW = "new"
    REMAINING = "remaining"
    CHANGED = "changed"


class ScoreDelta(BaseModel):
    previous: int = Field(..., description="Score in previous scan")
    current: int = Field(..., description="Score in current scan")
    delta: int = Field(..., description="Score change (current - previous)")


class PillarsDelta(BaseModel):
    security: ScoreDelta
    reliability: ScoreDelta
    code_quality: ScoreDelta
    performance: ScoreDelta
    architecture: ScoreDelta
    completeness: ScoreDelta


class FindingComparisonItem(BaseModel):
    status: FindingChangeStatus
    finding: NormalizedFinding
    previous_finding: Optional[NormalizedFinding] = None
    change_details: Optional[str] = None


class ComparisonSummary(BaseModel):
    fixed_count: int = 0
    new_count: int = 0
    remaining_count: int = 0
    changed_count: int = 0
    overall_delta: int = 0
    verdict: str = Field(..., description="'improved', 'regressed', or 'unchanged'")


class ComparisonReport(BaseModel):
    schema_version: str = Field(default="1.0")
    summary: ComparisonSummary
    overall: ScoreDelta
    pillars: PillarsDelta
    fixed_findings: List[NormalizedFinding] = Field(default_factory=list)
    new_findings: List[NormalizedFinding] = Field(default_factory=list)
    remaining_findings: List[NormalizedFinding] = Field(default_factory=list)
    changed_findings: List[FindingComparisonItem] = Field(default_factory=list)


class ComparisonRequest(BaseModel):
    previous_report: AnalysisReport
    current_report: AnalysisReport
