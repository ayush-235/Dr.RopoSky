"""Project Essentials Scanner adapter.

Validates the presence of standard engineering artifacts:
README, .gitignore, .env.example, LICENSE, and test suites.
Categorized as MISSING_ESSENTIAL / QUALITY (never as security vulnerabilities).
"""

import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from rokospy_analyzer.models.discovery import ProjectDiscovery
from rokospy_analyzer.models.finding import (
    CategoryEnum,
    SeverityEnum,
    ConfidenceEnum,
    NormalizedFinding,
)
from rokospy_analyzer.models.report import ScannerStatusEnum
from rokospy_analyzer.normalization.fingerprint import generate_finding_fingerprint
from rokospy_analyzer.scanners.base import BaseScanner


class ProjectEssentialsScanner(BaseScanner):
    """Deterministic validator for project essentials and repository completeness."""

    @property
    def name(self) -> str:
        return "rokospy-essentials"

    @property
    def supported_languages(self) -> List[str]:
        return ["All"]

    def is_available(self) -> bool:
        return True

    def is_applicable(self, discovery: ProjectDiscovery) -> bool:
        return discovery.total_file_count > 0

    def run(
        self, workspace_path: Path, discovery: ProjectDiscovery
    ) -> Tuple[ScannerStatusEnum, List[NormalizedFinding], Optional[str]]:
        findings: List[NormalizedFinding] = []

        # 1. Missing README
        if not discovery.has_readme:
            fp = generate_finding_fingerprint(self.name, "missing-readme", "README.md", 0, "Missing README.md")
            findings.append(
                NormalizedFinding(
                    id=str(uuid.uuid4()),
                    title="Missing Project Documentation (README.md)",
                    category=CategoryEnum.MISSING_ESSENTIAL,
                    severity=SeverityEnum.LOW,
                    file="README.md",
                    line=0,
                    column=0,
                    rule_id="missing-readme",
                    scanner=self.name,
                    message="No README.md documentation file found in project root. A README is essential for onboarding and project overview.",
                    evidence="No file matching README, README.md, or README.rst found.",
                    confidence=ConfidenceEnum.HIGH,
                    source=self.name,
                    fingerprint=fp,
                )
            )

        # 2. Missing .gitignore
        if not discovery.has_gitignore:
            fp = generate_finding_fingerprint(self.name, "missing-gitignore", ".gitignore", 0, "Missing .gitignore")
            findings.append(
                NormalizedFinding(
                    id=str(uuid.uuid4()),
                    title="Missing .gitignore File",
                    category=CategoryEnum.MISSING_ESSENTIAL,
                    severity=SeverityEnum.LOW,
                    file=".gitignore",
                    line=0,
                    column=0,
                    rule_id="missing-gitignore",
                    scanner=self.name,
                    message="No .gitignore file detected. A .gitignore ensures build artifacts, dependencies, and environment files are not committed.",
                    evidence="No .gitignore found in project root.",
                    confidence=ConfidenceEnum.HIGH,
                    source=self.name,
                    fingerprint=fp,
                )
            )

        # 3. Missing .env.example
        if not discovery.has_env_example:
            fp = generate_finding_fingerprint(self.name, "missing-env-example", ".env.example", 0, "Missing .env.example")
            findings.append(
                NormalizedFinding(
                    id=str(uuid.uuid4()),
                    title="Missing Environment Configuration Template (.env.example)",
                    category=CategoryEnum.MISSING_ESSENTIAL,
                    severity=SeverityEnum.LOW,
                    file=".env.example",
                    line=0,
                    column=0,
                    rule_id="missing-env-example",
                    scanner=self.name,
                    message="No .env.example or environment template detected. Templates document required environment variables safely without leaking secrets.",
                    evidence="No file matching .env.example, .env.sample, or .env.template found.",
                    confidence=ConfidenceEnum.HIGH,
                    source=self.name,
                    fingerprint=fp,
                )
            )

        # 4. Missing License
        if not discovery.has_license:
            fp = generate_finding_fingerprint(self.name, "missing-license", "LICENSE", 0, "Missing LICENSE")
            findings.append(
                NormalizedFinding(
                    id=str(uuid.uuid4()),
                    title="Missing Open Source License (LICENSE)",
                    category=CategoryEnum.MISSING_ESSENTIAL,
                    severity=SeverityEnum.INFO,
                    file="LICENSE",
                    line=0,
                    column=0,
                    rule_id="missing-license",
                    scanner=self.name,
                    message="No LICENSE file found. Providing an explicit license clarifies intellectual property and code distribution rights.",
                    evidence="No file matching LICENSE or LICENSE.md found.",
                    confidence=ConfidenceEnum.HIGH,
                    source=self.name,
                    fingerprint=fp,
                )
            )

        # 5. Missing Test Suite (Quality signal)
        if not discovery.has_tests:
            fp = generate_finding_fingerprint(self.name, "missing-tests", "tests/", 0, "Missing Automated Tests")
            findings.append(
                NormalizedFinding(
                    id=str(uuid.uuid4()),
                    title="Missing Automated Test Suite",
                    category=CategoryEnum.QUALITY,
                    severity=SeverityEnum.LOW,
                    file="tests/",
                    line=0,
                    column=0,
                    rule_id="missing-tests",
                    scanner=self.name,
                    message="No automated unit or integration tests detected in the repository.",
                    evidence="No test files (test_*.py, *.test.ts, *.spec.js, etc.) or test directories found.",
                    confidence=ConfidenceEnum.HIGH,
                    source=self.name,
                    fingerprint=fp,
                )
            )

        return ScannerStatusEnum.SUCCESS, findings, None
