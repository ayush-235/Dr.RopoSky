"""Pure deterministic scoring calculation functions."""

import math
from typing import List, Dict
from rokospy_analyzer.models.finding import NormalizedFinding, SeverityEnum
from rokospy_analyzer.scoring.config import ScoringConfig
from rokospy_analyzer.scoring.models import CategoryScore, ProjectScore


class ScoringCalculator:
    """Pure mathematical calculator for category deductions and weighted project scores."""

    @classmethod
    def get_rating_band(cls, score: int) -> str:
        """Determines the qualitative rating bracket according to 05_DESIGN.md."""
        if score >= 80:
            return "Strong Baseline"
        elif score >= 60:
            return "Needs Improvement"
        elif score >= 40:
            return "Significant Issues"
        else:
            return "Severe Issues"

    @classmethod
    def calculate_category_score(
        cls, pillar_name: str, findings: List[NormalizedFinding]
    ) -> CategoryScore:
        """
        Calculates the deterministic score (0-100) for a specific engineering pillar.
        """
        # Filter findings mapped to this pillar
        matching_findings = [
            f for f in findings
            if ScoringConfig.CATEGORY_MAPPING.get(
                f.category.value if hasattr(f.category, "value") else str(f.category), ""
            ) == pillar_name
        ]

        crit_count = 0
        high_count = 0
        med_count = 0
        low_count = 0
        info_count = 0
        total_deductions = 0

        for f in matching_findings:
            sev_str = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            penalty = ScoringConfig.SEVERITY_PENALTIES.get(sev_str, 0)
            total_deductions += penalty

            if sev_str == SeverityEnum.CRITICAL.value:
                crit_count += 1
            elif sev_str == SeverityEnum.HIGH.value:
                high_count += 1
            elif sev_str == SeverityEnum.MEDIUM.value:
                med_count += 1
            elif sev_str == SeverityEnum.LOW.value:
                low_count += 1
            elif sev_str == SeverityEnum.INFO.value:
                info_count += 1

        final_score = max(0, min(100, 100 - total_deductions))

        # Deterministic explanation
        if total_deductions == 0:
            explanation = "Perfect baseline: No issues detected in this pillar."
        else:
            parts = []
            if crit_count:
                parts.append(f"{crit_count} critical (-{crit_count * ScoringConfig.SEVERITY_PENALTIES['critical']} pts)")
            if high_count:
                parts.append(f"{high_count} high (-{high_count * ScoringConfig.SEVERITY_PENALTIES['high']} pts)")
            if med_count:
                parts.append(f"{med_count} medium (-{med_count * ScoringConfig.SEVERITY_PENALTIES['medium']} pts)")
            if low_count:
                parts.append(f"{low_count} low (-{low_count * ScoringConfig.SEVERITY_PENALTIES['low']} pts)")
            if info_count:
                parts.append(f"{info_count} info (-{info_count * ScoringConfig.SEVERITY_PENALTIES['info']} pts)")
            explanation = f"Score reduced by {total_deductions} pts due to: {', '.join(parts)}."

        return CategoryScore(
            category=pillar_name,
            score=final_score,
            finding_count=len(matching_findings),
            deductions=total_deductions,
            explanation=explanation,
        )

    @classmethod
    def calculate_project_score(cls, category_scores: Dict[str, CategoryScore]) -> ProjectScore:
        """
        Combines 6 category scores using deterministic weights into a ProjectScore (0-100).
        Uses standard round-half-up for mathematical consistency.
        """
        weighted_sum = 0.0
        for pillar_name, weight in ScoringConfig.CATEGORY_WEIGHTS.items():
            cat_score = category_scores.get(pillar_name)
            score_val = cat_score.score if cat_score else 100
            weighted_sum += score_val * weight

        overall_score = max(0, min(100, int(math.floor(weighted_sum + 0.5))))
        rating_band = cls.get_rating_band(overall_score)

        return ProjectScore(
            overall=overall_score,
            rating_band=rating_band,
            security=category_scores.get("security", CategoryScore(category="security", score=100)).score,
            reliability=category_scores.get("reliability", CategoryScore(category="reliability", score=100)).score,
            code_quality=category_scores.get("code_quality", CategoryScore(category="code_quality", score=100)).score,
            performance=category_scores.get("performance", CategoryScore(category="performance", score=100)).score,
            architecture=category_scores.get("architecture", CategoryScore(category="architecture", score=100)).score,
            completeness=category_scores.get("completeness", CategoryScore(category="completeness", score=100)).score,
            categories=category_scores,
        )
