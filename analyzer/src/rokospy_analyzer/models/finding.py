"""Normalized Finding models and enums for Rokospy Analyzer."""

from enum import Enum
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from rokospy_analyzer.ai.models import AIFindingEnrichment


class CategoryEnum(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    MISSING_ESSENTIAL = "missing_essential"
    ARCHITECTURE = "architecture"


class SeverityEnum(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ConfidenceEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NormalizedFinding(BaseModel):
    id: str = Field(..., description="Unique finding ID")
    title: str = Field(..., description="Short summary title of the issue")
    category: CategoryEnum = Field(..., description="Issue classification category")
    severity: SeverityEnum = Field(..., description="Normalized severity level")
    file: str = Field(..., description="Relative file path from project root")
    file_path: Optional[str] = Field(default=None, description="Alias for file")
    line: int = Field(default=1, ge=0, description="1-indexed line number (0 if whole-file/project)")
    line_number: Optional[int] = Field(default=None, description="Alias for line")
    column: int = Field(default=0, ge=0, description="1-indexed column number")
    column_number: Optional[int] = Field(default=None, description="Alias for column")
    rule_id: str = Field(..., description="Scanner-specific rule ID or signature")
    scanner: str = Field(..., description="Name of the detecting scanner")
    message: str = Field(..., description="Detailed description of what was detected")
    evidence: str = Field(default="", description="Sanitized source snippet or proof of finding")
    confidence: ConfidenceEnum = Field(default=ConfidenceEnum.HIGH, description="Detector confidence")
    source: str = Field(default="static_analysis", description="Detection source (e.g., tool name/rule)")
    fingerprint: str = Field(..., description="Deterministic hash for deduplication and tracking")
    enrichment: Optional[object] = Field(default=None, description="Optional AI explanation and fix enrichment")

    @model_validator(mode="after")
    def sync_aliases(self) -> "NormalizedFinding":
        if self.file_path is None:
            self.file_path = self.file
        if self.file is None or self.file == "":
            self.file = self.file_path or ""
        if self.line_number is None:
            self.line_number = self.line
        if self.column_number is None:
            self.column_number = self.column
        return self

    model_config = {
        "use_enum_values": True,
        "frozen": False,
    }

