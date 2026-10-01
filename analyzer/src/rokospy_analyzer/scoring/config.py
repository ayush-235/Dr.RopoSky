"""Configuration constants, severity weights, and category weights for deterministic scoring."""

from typing import Dict
from rokospy_analyzer.models.finding import CategoryEnum, SeverityEnum


class ScoringConfig:
    """Configurable weights and penalties for the deterministic scoring engine."""

    # Point deductions per finding severity
    SEVERITY_PENALTIES: Dict[str, int] = {
        SeverityEnum.CRITICAL.value: 25,
        SeverityEnum.HIGH.value: 15,
        SeverityEnum.MEDIUM.value: 8,
        SeverityEnum.LOW.value: 3,
        SeverityEnum.INFO.value: 1,
    }

    # Category weights for the overall project score (must sum to 1.0)
    CATEGORY_WEIGHTS: Dict[str, float] = {
        "security": 0.30,
        "reliability": 0.25,
        "code_quality": 0.15,
        "performance": 0.10,
        "architecture": 0.10,
        "completeness": 0.10,
    }

    # Mapping from NormalizedFinding.category to the 6 Scoring Pillars
    CATEGORY_MAPPING: Dict[str, str] = {
        CategoryEnum.SECURITY.value: "security",
        CategoryEnum.BUG.value: "reliability",
        CategoryEnum.QUALITY.value: "code_quality",
        CategoryEnum.PERFORMANCE.value: "performance",
        CategoryEnum.ARCHITECTURE.value: "architecture",
        CategoryEnum.MISSING_ESSENTIAL.value: "completeness",
    }
