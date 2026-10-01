"""Tests for FindingDeduplicator and fingerprint calculation."""

import uuid
from rokospy_analyzer.models.finding import (
    CategoryEnum,
    SeverityEnum,
    ConfidenceEnum,
    NormalizedFinding,
)
from rokospy_analyzer.normalization.deduplicator import FindingDeduplicator
from rokospy_analyzer.normalization.fingerprint import generate_finding_fingerprint


def test_deduplicate_identical_fingerprints():
    fp = generate_finding_fingerprint("scanner-a", "RULE-01", "src/app.py", 10, "Test Issue")

    f1 = NormalizedFinding(
        id=str(uuid.uuid4()),
        title="Test Issue",
        category=CategoryEnum.BUG,
        severity=SeverityEnum.MEDIUM,
        file="src/app.py",
        line=10,
        column=1,
        rule_id="RULE-01",
        scanner="scanner-a",
        message="Issue message 1",
        evidence="evidence 1",
        confidence=ConfidenceEnum.HIGH,
        source="scanner-a",
        fingerprint=fp,
    )

    f2 = NormalizedFinding(
        id=str(uuid.uuid4()),
        title="Test Issue",
        category=CategoryEnum.BUG,
        severity=SeverityEnum.HIGH,  # Higher severity should be retained
        file="src/app.py",
        line=10,
        column=1,
        rule_id="RULE-01",
        scanner="scanner-a",
        message="Issue message 2",
        evidence="evidence 2",
        confidence=ConfidenceEnum.HIGH,
        source="scanner-a",
        fingerprint=fp,
    )

    deduped = FindingDeduplicator.deduplicate([f1, f2])
    assert len(deduped) == 1
    assert deduped[0].severity == SeverityEnum.HIGH


def test_deduplicate_deterministic_ordering():
    f_low = NormalizedFinding(
        id=str(uuid.uuid4()),
        title="Low issue",
        category=CategoryEnum.QUALITY,
        severity=SeverityEnum.LOW,
        file="b.py",
        line=1,
        column=1,
        rule_id="R-LOW",
        scanner="sc",
        message="low",
        evidence="",
        confidence=ConfidenceEnum.LOW,
        source="sc",
        fingerprint="fp1",
    )

    f_crit = NormalizedFinding(
        id=str(uuid.uuid4()),
        title="Critical issue",
        category=CategoryEnum.SECURITY,
        severity=SeverityEnum.CRITICAL,
        file="a.py",
        line=1,
        column=1,
        rule_id="R-CRIT",
        scanner="sc",
        message="crit",
        evidence="",
        confidence=ConfidenceEnum.HIGH,
        source="sc",
        fingerprint="fp2",
    )

    deduped = FindingDeduplicator.deduplicate([f_low, f_crit])
    assert len(deduped) == 2
    # Critical must be sorted before Low
    assert deduped[0].severity == SeverityEnum.CRITICAL
    assert deduped[1].severity == SeverityEnum.LOW
