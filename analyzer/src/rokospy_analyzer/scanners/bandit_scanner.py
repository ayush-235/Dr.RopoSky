"""Bandit Scanner adapter for Python security vulnerabilities."""

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


class BanditScanner(BaseScanner):
    """Adapter for Bandit Python SAST security scanner."""

    @property
    def name(self) -> str:
        return "bandit"

    @property
    def supported_languages(self) -> List[str]:
        return ["Python"]

    def is_available(self) -> bool:
        return shutil.which("bandit") is not None

    def is_applicable(self, discovery: ProjectDiscovery) -> bool:
        return "Python" in discovery.detected_languages

    def run(
        self, workspace_path: Path, discovery: ProjectDiscovery
    ) -> Tuple[ScannerStatusEnum, List[NormalizedFinding], Optional[str]]:
        if not self.is_available():
            return (
                ScannerStatusEnum.UNAVAILABLE,
                [],
                "Bandit binary is not installed in system PATH (install with 'pip install bandit')",
            )

        cmd = ["bandit", "-r", ".", "-f", "json", "-q", "--exclude", "tests,test,.venv,venv"]
        retcode, stdout, stderr = self._execute_subprocess(cmd, workspace_path)

        # Bandit returns exit code 0 (no issues) or 1 (issues found)
        if not stdout.strip() and retcode not in {0, 1}:
            return ScannerStatusEnum.FAILED, [], f"Bandit execution failed: {stderr}"

        try:
            data = json.loads(stdout) if stdout.strip() else {"results": []}
        except json.JSONDecodeError as e:
            return ScannerStatusEnum.FAILED, [], f"Failed to parse Bandit JSON output: {str(e)}"

        findings = self._normalize_bandit(data, workspace_path)
        return ScannerStatusEnum.SUCCESS, findings, None

    def _normalize_bandit(self, data: dict, workspace_path: Path) -> List[NormalizedFinding]:
        findings: List[NormalizedFinding] = []
        raw_results = data.get("results", [])

        severity_map = {
            "HIGH": SeverityEnum.HIGH,
            "MEDIUM": SeverityEnum.MEDIUM,
            "LOW": SeverityEnum.LOW,
        }

        confidence_map = {
            "HIGH": ConfidenceEnum.HIGH,
            "MEDIUM": ConfidenceEnum.MEDIUM,
            "LOW": ConfidenceEnum.LOW,
        }

        for item in raw_results:
            rule_id = item.get("test_id", "B000")
            test_name = item.get("test_name", "bandit_check")
            raw_file = item.get("filename", "")
            try:
                rel_file = str(Path(raw_file).relative_to(workspace_path)).replace("\\", "/")
            except Exception:
                rel_file = str(Path(raw_file)).replace("\\", "/")

            line_num = int(item.get("line_number", 1))
            raw_sev = item.get("issue_severity", "MEDIUM").upper()
            raw_conf = item.get("issue_confidence", "MEDIUM").upper()
            issue_text = item.get("issue_text", "Security issue detected by Bandit")
            code_snippet = item.get("code", "")

            # Escalate critical vulnerabilities (e.g. hardcoded passwords, shell injections)
            normalized_sev = severity_map.get(raw_sev, SeverityEnum.MEDIUM)
            if "hardcoded_password" in test_name or "exec_used" in test_name:
                normalized_sev = SeverityEnum.CRITICAL

            title = f"Python Security: {issue_text.splitlines()[0]}"
            sanitized_evidence = SecretRedactor.redact(code_snippet)
            sanitized_message = SecretRedactor.redact(issue_text)

            fp = generate_finding_fingerprint(
                scanner=self.name,
                rule_id=rule_id,
                file_path=rel_file,
                line=line_num,
                title=title,
            )

            findings.append(
                NormalizedFinding(
                    id=str(uuid.uuid4()),
                    title=title,
                    category=CategoryEnum.SECURITY,
                    severity=normalized_sev,
                    file=rel_file,
                    line=line_num,
                    column=1,
                    rule_id=f"bandit-{rule_id}",
                    scanner=self.name,
                    message=sanitized_message,
                    evidence=sanitized_evidence,
                    confidence=confidence_map.get(raw_conf, ConfidenceEnum.MEDIUM),
                    source=self.name,
                    fingerprint=fp,
                )
            )

        return findings
