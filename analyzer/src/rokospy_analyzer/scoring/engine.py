"""High-level scoring orchestrator for Rokospy."""

from typing import List, Dict
from rokospy_analyzer.models.finding import NormalizedFinding
from rokospy_analyzer.scoring.calculator import ScoringCalculator
from rokospy_analyzer.scoring.config import ScoringConfig
from rokospy_analyzer.scoring.models import CategoryScore, ProjectScore


class ScoringEngine:
    """Orchestrates deterministic 6-pillar scoring on deduplicated findings."""

    @classmethod
    def evaluate(cls, findings: List[NormalizedFinding]) -> ProjectScore:
        """
        Evaluates deduplicated findings across all 6 core pillars:
        1. Security
        2. Reliability
        3. Code Quality
        4. Performance
        5. Architecture
        6. Completeness
        """
        category_scores: Dict[str, CategoryScore] = {}

        for pillar_name in ScoringConfig.CATEGORY_WEIGHTS.keys():
            cat_score = ScoringCalculator.calculate_category_score(pillar_name, findings)
            category_scores[pillar_name] = cat_score

        return ScoringCalculator.calculate_project_score(category_scores)
