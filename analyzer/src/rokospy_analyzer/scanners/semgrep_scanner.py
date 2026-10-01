"""Semgrep Scanner adapter for multi-language static analysis and security scanning."""

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


class SemgrepScanner(BaseScanner):
    """Adapter for Semgrep multi-language static and security analyzer."""

    @property
    def name(self) -> str:
        return "semgrep"

    @property
    def supported_languages(self) -> List[str]:
        return ["Python", "JavaScript", "TypeScript"]

    def is_available(self) -> bool:
        return shutil.which("semgrep") is not None

    def is_applicable(self, discovery: ProjectDiscovery) -> bool:
        return bool(set(discovery.detected_languages).intersection({"Python", "JavaScript", "TypeScript"}))

    def run(
        self, workspace_path: Path, discovery: ProjectDiscovery
    ) -> Tuple[ScannerStatusEnum, List[NormalizedFinding], Optional[str]]:
        if not self.is_available():
            return (
                ScannerStatusEnum.UNAVAILABLE,
                [],
                "Semgrep binary is not installed in system PATH (install with 'pip install semgrep')",
            )

        cmd = [
            "semgrep",
            "--json",
            "--config", "p/default",
            "--quiet",
            "--no-git-ignore",
            "--exclude", "node_modules",
            "--exclude", ".venv",
            "--exclude", "dist",
            str(workspace_path),
        ]

        retcode, stdout, stderr = self._execute_subprocess(cmd, workspace_path)

        if not stdout.strip() and retcode not in {0, 1}:
            return ScannerStatusEnum.FAILED, [], f"Semgrep execution failed: {stderr}"

        try:
            data = json.loads(stdout) if stdout.strip() else {"results": []}
        except json.JSONDecodeError as e:
            return ScannerStatusEnum.FAILED, [], f"Failed to parse Semgrep JSON output: {str(e)}"

        findings = self._normalize_semgrep(data, workspace_path)
        return ScannerStatusEnum.SUCCESS, findings, None

    def _normalize_semgrep(self, data: dict, workspace_path: Path) -> List[NormalizedFinding]:
        findings: List[NormalizedFinding] = []
        raw_results = data.get("results", [])

        sev_map = {
            "ERROR": SeverityEnum.HIGH,
            "WARNING": SeverityEnum.MEDIUM,
            "INFO": SeverityEnum.LOW,
        }

        for item in raw_results:
            rule_id = item.get("check_id", "semgrep-rule")
            raw_path = item.get("path", "")
            try:
                rel_file = str(Path(raw_path).relative_to(workspace_path)).replace("\\", "/")
            except Exception:
                rel_file = str(Path(raw_path)).replace("\\", "/")

            start = item.get("start", {})
            line_num = int(start.get("line", 1))
            col_num = int(start.get("col", 1))

            extra = item.get("extra", {})
            message = extra.get("message", "Issue detected by Semgrep")
            raw_sev = extra.get("severity", "WARNING").upper()
            metadata = extra.get("metadata", {})
            raw_category = metadata.get("category", "").lower()
            confidence_str = metadata.get("confidence", "HIGH").upper()

            # Map category
            category = CategoryEnum.BUG
            if "security" in raw_category or "cwe" in metadata or "owasp" in metadata:
                category = CategoryEnum.SECURITY
            elif "performance" in raw_category:
                category = CategoryEnum.PERFORMANCE
            elif "quality" in raw_category or "maintainability" in raw_category:
                category = CategoryEnum.QUALITY

            # Determine severity
            severity = sev_map.get(raw_sev, SeverityEnum.MEDIUM)
            if category == CategoryEnum.SECURITY and raw_sev == "ERROR":
                severity = SeverityEnum.CRITICAL

            # Extract lines
            lines_snippet = extra.get("lines", "")
            sanitized_evidence = SecretRedactor.redact(lines_snippet)
            sanitized_message = SecretRedactor.redact(message)

            title = f"Semgrep: {rule_id.split('.')[-1].replace('-', ' ').title()}"

            fp = generate_finding_fingerprint(
                scanner=self.name,
                rule_id=rule_id,
                file_path=rel_file,
                line=line_num,
                title=title,
            )

            confidence = ConfidenceEnum.HIGH
            if confidence_str == "MEDIUM":
                confidence = ConfidenceEnum.MEDIUM
            elif confidence_str == "LOW":
                confidence = ConfidenceEnum.LOW

            findings.append(
                NormalizedFinding(
                    id=str(uuid.uuid4()),
                    title=title,
                    category=category,
                    severity=severity,
                    file=rel_file,
                    line=line_num,
                    column=col_num,
                    rule_id=rule_id,
                    scanner=self.name,
                    message=sanitized_message,
                    evidence=sanitized_evidence,
                    confidence=confidence,
                    source=self.name,
                    fingerprint=fp,
                )
            )

        return findings
