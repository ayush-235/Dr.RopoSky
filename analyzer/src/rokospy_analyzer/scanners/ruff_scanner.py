"""Ruff Scanner adapter for Python fast linting, syntax, and bug detection."""

import json
import shutil
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
from rokospy_analyzer.security.redactor import SecretRedactor


class RuffScanner(BaseScanner):
    """Adapter for Ruff Python fast linter and bug detector."""

    @property
    def name(self) -> str:
        return "ruff"

    @property
    def supported_languages(self) -> List[str]:
        return ["Python"]

    def is_available(self) -> bool:
        return shutil.which("ruff") is not None

    def is_applicable(self, discovery: ProjectDiscovery) -> bool:
        return "Python" in discovery.detected_languages

    def run(
        self, workspace_path: Path, discovery: ProjectDiscovery
    ) -> Tuple[ScannerStatusEnum, List[NormalizedFinding], Optional[str]]:
        if not self.is_available():
            return (
                ScannerStatusEnum.UNAVAILABLE,
                [],
                "Ruff binary is not installed in system PATH (install with 'pip install ruff')",
            )

        cmd = [
            "ruff",
            "check",
            ".",
            "--output-format", "json",
            "--exclude", ".venv,venv,node_modules,dist,build",
        ]

        retcode, stdout, stderr = self._execute_subprocess(cmd, workspace_path)

        if not stdout.strip() and retcode not in {0, 1}:
            return ScannerStatusEnum.FAILED, [], f"Ruff execution failed: {stderr}"

        try:
            data = json.loads(stdout) if stdout.strip() else []
        except json.JSONDecodeError as e:
            return ScannerStatusEnum.FAILED, [], f"Failed to parse Ruff JSON output: {str(e)}"

        findings = self._normalize_ruff(data, workspace_path)
        return ScannerStatusEnum.SUCCESS, findings, None

    def _normalize_ruff(self, data: list, workspace_path: Path) -> List[NormalizedFinding]:
        findings: List[NormalizedFinding] = []

        for item in data:
            code = item.get("code", "E000")
            message = item.get("message", "Lint issue detected by Ruff")
            raw_file = item.get("filename", "")
            try:
                rel_file = str(Path(raw_file).relative_to(workspace_path)).replace("\\", "/")
            except Exception:
                rel_file = str(Path(raw_file)).replace("\\", "/")

            location = item.get("location", {})
            line_num = int(location.get("row", 1))
            col_num = int(location.get("column", 1))

            # Categorize based on Ruff prefix
            category = CategoryEnum.QUALITY
            severity = SeverityEnum.LOW

            if code.startswith("F") or code.startswith("E9"):  # Pyflakes undefined names / syntax errors
                category = CategoryEnum.BUG
                severity = SeverityEnum.HIGH
            elif code.startswith("B"):  # Bugbear logic bugs
                category = CategoryEnum.BUG
                severity = SeverityEnum.MEDIUM
            elif code.startswith("S"):  # Bandit security rules in Ruff
                category = CategoryEnum.SECURITY
                severity = SeverityEnum.HIGH
            elif code.startswith("PERF"):  # Performance
                category = CategoryEnum.PERFORMANCE
                severity = SeverityEnum.MEDIUM

            title = f"Python {category.title()}: {message}"
            sanitized_message = SecretRedactor.redact(message)

            fp = generate_finding_fingerprint(
                scanner=self.name,
                rule_id=code,
                file_path=rel_file,
                line=line_num,
                title=title,
            )

            findings.append(
                NormalizedFinding(
                    id=str(uuid.uuid4()),
                    title=title,
                    category=category,
                    severity=severity,
                    file=rel_file,
                    line=line_num,
                    column=col_num,
                    rule_id=f"ruff-{code}",
                    scanner=self.name,
                    message=sanitized_message,
                    evidence=f"Line {line_num}: {sanitized_message}",
                    confidence=ConfidenceEnum.HIGH,
                    source=self.name,
                    fingerprint=fp,
                )
            )

        return findings
