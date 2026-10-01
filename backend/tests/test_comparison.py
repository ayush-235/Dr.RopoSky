"""Tests for Phase 7 Deterministic Comparison Engine & API."""

import pytest
from fastapi.testclient import TestClient
from rokospy_analyzer.models.finding import CategoryEnum, NormalizedFinding, SeverityEnum
from rokospy_analyzer.models.report import (
    AnalysisExecutionInfo,
    AnalysisReport,
    CategorySummary,
    ProjectMetadata,
    SeveritySummary,
)
from rokospy_analyzer.scoring.models import CategoryScore, ProjectScore
from app.services.comparison_service import ComparisonEngine


def make_report(
    overall: int,
    findings: list[NormalizedFinding],
    security_score: int = 100,
    reliability_score: int = 100,
) -> AnalysisReport:
    """Helper to build a deterministic AnalysisReport fixture."""
    return AnalysisReport(
        schema_version="1.0",
        project=ProjectMetadata(
            name="test-project",
            source_type="git",
            languages=["Python"],
            manifests=["pyproject.toml"],
        ),
        analysis=AnalysisExecutionInfo(duration_ms=500, files_analyzed=10),
        scanners=[],
        findings=findings,
        summary=SeveritySummary(critical=len([f for f in findings if f.severity == SeverityEnum.CRITICAL])),
        category_summary=CategorySummary(),
        score=ProjectScore(
            overall=overall,
            rating_band="Strong Baseline" if overall >= 80 else "Needs Improvement",
            security=security_score,
            reliability=reliability_score,
            code_quality=100,
            performance=100,
            architecture=100,
            completeness=100,
            categories={
                "security": CategoryScore(category="security", score=security_score),
                "reliability": CategoryScore(category="reliability", score=reliability_score),
            },
        ),
    )


def test_identical_reports_comparison():
    """Identical reports yield 0 fixed, 0 new, N remaining, 0 delta, unchanged verdict."""
    f1 = NormalizedFinding(
        id="f1",
        title="Uncaught Exception",
        message="Potential NoneType error",
        severity=SeverityEnum.MEDIUM,
        category=CategoryEnum.BUG,
        file="src/main.py",
        line=20,
        rule_id="semgrep-001",
        scanner="semgrep",
        evidence="user.name.lower()",
        fingerprint="fp1",
    )
    rep1 = make_report(75, [f1])
    rep2 = make_report(75, [f1])

    result = ComparisonEngine.compare_reports(rep1, rep2)
    assert result.summary.fixed_count == 0
    assert result.summary.new_count == 0
    assert result.summary.remaining_count == 1
    assert result.summary.overall_delta == 0
    assert result.summary.verdict == "unchanged"


def test_fixed_vulnerability_detection():
    """Vulnerability present in previous report but absent in current is classified as FIXED with positive delta."""
    f_vuln = NormalizedFinding(
        id="sec1",
        title="Hardcoded Secret Key",
        message="AWS key found",
        severity=SeverityEnum.CRITICAL,
        category=CategoryEnum.SECURITY,
        file="src/config.py",
        line=10,
        rule_id="secret-001",
        scanner="rokospy-secret-scanner",
        evidence="AWS_SECRET = '[REDACTED_SECRET]'",
        fingerprint="fp_sec",
    )
    rep_prev = make_report(50, [f_vuln], security_score=50)
    rep_curr = make_report(100, [], security_score=100)

    result = ComparisonEngine.compare_reports(rep_prev, rep_curr)
    assert result.summary.fixed_count == 1
    assert result.summary.new_count == 0
    assert result.summary.remaining_count == 0
    assert result.summary.overall_delta == 50
    assert result.summary.verdict == "improved"
    assert result.pillars.security.delta == 50
    assert len(result.fixed_findings) == 1
    assert result.fixed_findings[0].title == "Hardcoded Secret Key"


def test_new_vulnerability_detection():
    """Vulnerability absent in previous report but present in current is classified as NEW with negative delta."""
    f_new = NormalizedFinding(
        id="sec2",
        title="SQL Injection",
        message="Raw query formatting",
        severity=SeverityEnum.HIGH,
        category=CategoryEnum.SECURITY,
        file="src/db.py",
        line=45,
        rule_id="bandit-b608",
        scanner="bandit",
        evidence="cursor.execute(f'SELECT * FROM users WHERE id = {uid}')",
        fingerprint="fp_sql",
    )
    rep_prev = make_report(100, [], security_score=100)
    rep_curr = make_report(70, [f_new], security_score=70)

    result = ComparisonEngine.compare_reports(rep_prev, rep_curr)
    assert result.summary.fixed_count == 0
    assert result.summary.new_count == 1
    assert result.summary.remaining_count == 0
    assert result.summary.overall_delta == -30
    assert result.summary.verdict == "regressed"
    assert result.pillars.security.delta == -30
    assert len(result.new_findings) == 1


def test_line_number_movement_stable_matching():
    """Harmless line number movement (e.g. line 10 -> 35) retains stable identity as REMAINING instead of FIXED+NEW."""
    f_prev = NormalizedFinding(
        id="f10",
        title="Uncaught TypeError",
        message="None access",
        severity=SeverityEnum.MEDIUM,
        category=CategoryEnum.BUG,
        file="src/utils.py",
        line=10,
        rule_id="semgrep-type",
        scanner="semgrep",
        evidence="return data.get('val').strip()",
        fingerprint="fp_same",
    )
    f_curr = NormalizedFinding(
        id="f35",
        title="Uncaught TypeError",
        message="None access",
        severity=SeverityEnum.MEDIUM,
        category=CategoryEnum.BUG,
        file="src/utils.py",
        line=35,  # Line moved by 25 lines
        rule_id="semgrep-type",
        scanner="semgrep",
        evidence="return data.get('val').strip()",
        fingerprint="fp_same",
    )
    rep_prev = make_report(80, [f_prev])
    rep_curr = make_report(80, [f_curr])

    result = ComparisonEngine.compare_reports(rep_prev, rep_curr)
    assert result.summary.fixed_count == 0
    assert result.summary.new_count == 0
    assert result.summary.remaining_count == 1


def test_severity_change_detection():
    """Change in finding severity is classified into changed_findings."""
    f_prev = NormalizedFinding(
        id="f_prev",
        title="Insecure Cookie",
        message="Cookie missing Secure flag",
        severity=SeverityEnum.LOW,
        category=CategoryEnum.SECURITY,
        file="src/server.py",
        line=12,
        rule_id="cookie-001",
        scanner="semgrep",
        evidence="response.set_cookie('session', sid)",
        fingerprint="fp_cookie",
    )
    f_curr = NormalizedFinding(
        id="f_curr",
        title="Insecure Cookie",
        message="Cookie missing Secure flag",
        severity=SeverityEnum.HIGH,  # Upgraded severity
        category=CategoryEnum.SECURITY,
        file="src/server.py",
        line=12,
        rule_id="cookie-001",
        scanner="semgrep",
        evidence="response.set_cookie('session', sid)",
        fingerprint="fp_cookie",
    )
    rep_prev = make_report(95, [f_prev], security_score=95)
    rep_curr = make_report(75, [f_curr], security_score=75)

    result = ComparisonEngine.compare_reports(rep_prev, rep_curr)
    assert result.summary.changed_count == 1
    assert result.summary.remaining_count == 0
    assert len(result.changed_findings) == 1
    assert "LOW to HIGH" in (result.changed_findings[0].change_details or "")


def test_post_compare_api_endpoint(client: TestClient):
    """POST /api/v1/compare endpoint accepts two valid reports and returns structured ComparisonReport."""
    f1 = NormalizedFinding(
        id="f1",
        title="Sample Finding",
        message="Test message",
        severity=SeverityEnum.LOW,
        category=CategoryEnum.QUALITY,
        file="app.py",
        line=1,
        rule_id="ruff-001",
        scanner="ruff",
        fingerprint="fp1",
    )
    rep1 = make_report(80, [f1])
    rep2 = make_report(100, [])

    payload = {
        "previous_report": rep1.model_dump(),
        "current_report": rep2.model_dump(),
    }

    response = client.post("/api/v1/compare", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["schema_version"] == "1.0"
    assert data["summary"]["fixed_count"] == 1
    assert data["summary"]["overall_delta"] == 20
    assert data["summary"]["verdict"] == "improved"
    assert data["overall"]["previous"] == 80
    assert data["overall"]["current"] == 100
    assert data["overall"]["delta"] == 20
    assert len(data["fixed_findings"]) == 1


def test_empty_and_clean_reports_comparison():
    """Comparison handles empty findings lists cleanly with 0 deltas and zero counts."""
    rep_clean1 = make_report(100, [])
    rep_clean2 = make_report(100, [])

    result = ComparisonEngine.compare_reports(rep_clean1, rep_clean2)
    assert result.summary.fixed_count == 0
    assert result.summary.new_count == 0
    assert result.summary.remaining_count == 0
    assert result.summary.changed_count == 0
    assert result.summary.overall_delta == 0
    assert result.summary.verdict == "unchanged"


def test_ai_enrichment_invariance_in_comparison():
    """AI enrichment presence or difference does not alter deterministic finding identity."""
    from rokospy_analyzer.ai.models import AIFindingEnrichment

    f_prev = NormalizedFinding(
        id="sec1",
        title="Hardcoded Secret Key",
        message="AWS key found",
        severity=SeverityEnum.CRITICAL,
        category=CategoryEnum.SECURITY,
        file="src/config.py",
        line=10,
        rule_id="secret-001",
        scanner="rokospy-secret-scanner",
        evidence="AWS_SECRET = '[REDACTED_SECRET]'",
        fingerprint="fp_sec",
        enrichment=None,
    )
    f_curr = NormalizedFinding(
        id="sec1",
        title="Hardcoded Secret Key",
        message="AWS key found",
        severity=SeverityEnum.CRITICAL,
        category=CategoryEnum.SECURITY,
        file="src/config.py",
        line=10,
        rule_id="secret-001",
        scanner="rokospy-secret-scanner",
        evidence="AWS_SECRET = '[REDACTED_SECRET]'",
        fingerprint="fp_sec",
        enrichment=AIFindingEnrichment(
            finding_id="sec1",
            explanation="Different AI explanation text",
            why_it_matters="Critical risk",
            fix_steps=["Rotate key"],
            confidence_score=0.99,
        ),
    )
    rep1 = make_report(50, [f_prev])
    rep2 = make_report(50, [f_curr])

    result = ComparisonEngine.compare_reports(rep1, rep2)
    assert result.summary.fixed_count == 0
    assert result.summary.new_count == 0
    assert result.summary.remaining_count == 1
    assert result.summary.changed_count == 0


def test_post_compare_invalid_payload(client: TestClient):
    """POST /api/v1/compare returns 422 Unprocessable Entity for invalid or missing reports."""
    response = client.post("/api/v1/compare", json={"previous_report": {}})
    assert response.status_code == 422

