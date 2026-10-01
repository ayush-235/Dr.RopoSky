"""Tests for Phase 3 Deterministic Scoring and Report Engine."""

import uuid
from pathlib import Path
import pytest
from rokospy_analyzer.ai.models import AIFindingEnrichment, AIConfidenceEnum, AIStatusEnum
from rokospy_analyzer.models.finding import (
    CategoryEnum,
    SeverityEnum,
    ConfidenceEnum,
    NormalizedFinding,
)
from rokospy_analyzer.pipeline import AnalyzerPipeline
from rokospy_analyzer.scoring.calculator import ScoringCalculator
from rokospy_analyzer.scoring.config import ScoringConfig
from rokospy_analyzer.scoring.engine import ScoringEngine


def _make_finding(category: CategoryEnum, severity: SeverityEnum, title: str = "Issue") -> NormalizedFinding:
    return NormalizedFinding(
        id=str(uuid.uuid4()),
        title=title,
        category=category,
        severity=severity,
        file="src/app.py",
        line=10,
        column=1,
        rule_id="RULE-01",
        scanner="test-scanner",
        message="Test issue message",
        evidence="code evidence",
        confidence=ConfidenceEnum.HIGH,
        source="test-scanner",
        fingerprint=f"fp-{uuid.uuid4().hex[:8]}",
    )


def test_clean_project_score():
    """A clean project with 0 findings receives 100 in all 6 pillars and 100 overall."""
    score = ScoringEngine.evaluate([])
    assert score.overall == 100
    assert score.rating_band == "Strong Baseline"
    assert score.security == 100
    assert score.reliability == 100
    assert score.code_quality == 100
    assert score.performance == 100
    assert score.architecture == 100
    assert score.completeness == 100
    for cat in score.categories.values():
        assert cat.score == 100
        assert cat.deductions == 0
        assert cat.finding_count == 0


def test_single_critical_security_deduction():
    """A critical security finding deducts 25 points from Security pillar."""
    f = _make_finding(CategoryEnum.SECURITY, SeverityEnum.CRITICAL, "Critical SQLi")
    score = ScoringEngine.evaluate([f])

    assert score.security == 75  # 100 - 25
    assert score.reliability == 100
    assert score.code_quality == 100
    # Weighted overall: 75 * 0.30 + 100 * 0.70 = 22.5 + 70 = 92.5 -> 93
    assert score.overall == 93
    assert score.rating_band == "Strong Baseline"


def test_score_clamping_to_zero():
    """Severe accumulated penalties cannot drive category or overall scores below 0."""
    # 10 critical security findings = -250 points
    findings = [_make_finding(CategoryEnum.SECURITY, SeverityEnum.CRITICAL) for _ in range(10)]
    score = ScoringEngine.evaluate(findings)

    assert score.security == 0
    assert score.categories["security"].deductions == 250
    assert score.overall >= 0


def test_category_mapping_isolation():
    """Findings in one category do not bleed penalties into unrelated categories."""
    f_bug = _make_finding(CategoryEnum.BUG, SeverityEnum.HIGH)  # -15 Reliability
    f_perf = _make_finding(CategoryEnum.PERFORMANCE, SeverityEnum.MEDIUM)  # -8 Performance
    f_miss = _make_finding(CategoryEnum.MISSING_ESSENTIAL, SeverityEnum.LOW)  # -3 Completeness

    score = ScoringEngine.evaluate([f_bug, f_perf, f_miss])

    assert score.security == 100  # Untouched
    assert score.architecture == 100  # Untouched
    assert score.code_quality == 100  # Untouched
    assert score.reliability == 85  # 100 - 15
    assert score.performance == 92  # 100 - 8
    assert score.completeness == 97  # 100 - 3


def test_ai_invariance_on_score():
    """
    CRITICAL RULE: AI explanation, confidence, or wording must NOT affect the deterministic score.
    """
    f1 = _make_finding(CategoryEnum.SECURITY, SeverityEnum.HIGH, "Hardcoded Secret")
    f1.enrichment = AIFindingEnrichment(
        why_it_matters="AI explanation version A",
        impact="Impact text A",
        fix_steps=["Step 1"],
        confidence=AIConfidenceEnum.HIGH,
        status=AIStatusEnum.SUCCESS,
    )

    f2 = _make_finding(CategoryEnum.SECURITY, SeverityEnum.HIGH, "Hardcoded Secret")
    f2.enrichment = AIFindingEnrichment(
        why_it_matters="Completely different AI text",
        impact="Totally different impact",
        fix_steps=["Alternative steps"],
        confidence=AIConfidenceEnum.LOW,  # Different confidence
        status=AIStatusEnum.FAILED,
    )

    score_1 = ScoringEngine.evaluate([f1])
    score_2 = ScoringEngine.evaluate([f2])

    assert score_1.overall == score_2.overall
    assert score_1.security == score_2.security
    assert score_1.reliability == score_2.reliability
    assert score_1.code_quality == score_2.code_quality


def test_score_reproducibility():
    """Running the scoring engine 10 times on the same finding set yields identical scores."""
    findings = [
        _make_finding(CategoryEnum.SECURITY, SeverityEnum.HIGH),
        _make_finding(CategoryEnum.BUG, SeverityEnum.MEDIUM),
        _make_finding(CategoryEnum.MISSING_ESSENTIAL, SeverityEnum.LOW),
    ]

    baseline = ScoringEngine.evaluate(findings)
    for _ in range(10):
        current = ScoringEngine.evaluate(findings)
        assert current.overall == baseline.overall
        assert current.security == baseline.security
        assert current.reliability == baseline.reliability
        assert current.code_quality == baseline.code_quality
        assert current.performance == baseline.performance
        assert current.architecture == baseline.architecture
        assert current.completeness == baseline.completeness


def test_rating_band_thresholds():
    assert ScoringCalculator.get_rating_band(100) == "Strong Baseline"
    assert ScoringCalculator.get_rating_band(80) == "Strong Baseline"
    assert ScoringCalculator.get_rating_band(79) == "Needs Improvement"
    assert ScoringCalculator.get_rating_band(60) == "Needs Improvement"
    assert ScoringCalculator.get_rating_band(59) == "Significant Issues"
    assert ScoringCalculator.get_rating_band(40) == "Significant Issues"
    assert ScoringCalculator.get_rating_band(39) == "Severe Issues"
    assert ScoringCalculator.get_rating_band(0) == "Severe Issues"


def test_e2e_pipeline_scoring_integration(tmp_path: Path):
    """End-to-end integration: AnalyzerPipeline generates score within AnalysisReport."""
    proj_dir = tmp_path / "test_app"
    proj_dir.mkdir()
    (proj_dir / "README.md").write_text("# Test App\n")
    (proj_dir / ".gitignore").write_text(".venv/\n")
    (proj_dir / ".env.example").write_text("KEY=\n")
    (proj_dir / "LICENSE").write_text("MIT\n")
    (proj_dir / "index.py").write_text("print('clean code')\n")

    report = AnalyzerPipeline.analyze(str(proj_dir))
    assert report.schema_version == "1.0"
    assert report.score is not None
    assert isinstance(report.score.overall, int)
    assert 0 <= report.score.overall <= 100
    assert "security" in report.score.categories
    assert "reliability" in report.score.categories
    assert "code_quality" in report.score.categories
    assert "performance" in report.score.categories
    assert "architecture" in report.score.categories
    assert "completeness" in report.score.categories
