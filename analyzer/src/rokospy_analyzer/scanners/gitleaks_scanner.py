"""Gitleaks Scanner adapter for secret and credential detection in code and Git history."""

import json
import shutil
import tempfile
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


class GitleaksScanner(BaseScanner):
    """Adapter for the external Gitleaks CLI scanner."""

    @property
    def name(self) -> str:
        return "gitleaks"

    @property
    def supported_languages(self) -> List[str]:
        return ["All"]

    def is_available(self) -> bool:
        return shutil.which("gitleaks") is not None

    def is_applicable(self, discovery: ProjectDiscovery) -> bool:
        return discovery.total_file_count > 0

    def run(
        self, workspace_path: Path, discovery: ProjectDiscovery
    ) -> Tuple[ScannerStatusEnum, List[NormalizedFinding], Optional[str]]:
        if not self.is_available():
            return (
                ScannerStatusEnum.UNAVAILABLE,
                [],
                "Gitleaks binary is not installed or not found in system PATH",
            )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as report_file:
            report_path = Path(report_file.name)

        try:
            # Run gitleaks with no-git flag if not a git repo or directory scan
            cmd = [
                "gitleaks",
                "detect",
                "--source", str(workspace_path),
                "--report-format", "json",
                "--report-path", str(report_path),
                "--no-banner",
            ]
            if not discovery.has_git_history:
                cmd.append("--no-git")

            retcode, stdout, stderr = self._execute_subprocess(cmd, workspace_path)

            findings: List[NormalizedFinding] = []
            if report_path.exists() and report_path.stat().st_size > 0:
                try:
                    data = json.loads(report_path.read_text(encoding="utf-8", errors="ignore"))
                    findings = self._normalize_gitleaks(data, workspace_path)
                except json.JSONDecodeError as e:
                    return ScannerStatusEnum.FAILED, [], f"Failed to parse Gitleaks JSON: {str(e)}"

            return ScannerStatusEnum.SUCCESS, findings, None

        finally:
            if report_path.exists():
                report_path.unlink(missing_ok=True)

    def _normalize_gitleaks(self, data: list, workspace_path: Path) -> List[NormalizedFinding]:
        findings: List[NormalizedFinding] = []
        for item in data:
            rule_id = item.get("RuleID", "gitleaks-secret")
            desc = item.get("Description", "Detected hardcoded secret")
            raw_file = item.get("File", "unknown")
            try:
                rel_file = str(Path(raw_file).relative_to(workspace_path)).replace("\\", "/")
            except Exception:
                rel_file = str(Path(raw_file)).replace("\\", "/")

            line_num = int(item.get("StartLine", 1))
            col_num = int(item.get("StartColumn", 1))

            # Secret redaction on secret match
            raw_match = item.get("Match", "")
            sanitized_evidence = SecretRedactor.redact(raw_match) or SecretRedactor.redact(item.get("Secret", ""))

            title = f"Exposed Secret: {desc}"
            message = f"Gitleaks detected a sensitive credential ({desc}). Immediately rotate and remove."

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
                    severity=SeverityEnum.CRITICAL,
                    file=rel_file,
                    line=line_num,
                    column=col_num,
                    rule_id=rule_id,
                    scanner=self.name,
                    message=message,
                    evidence=sanitized_evidence,
                    confidence=ConfidenceEnum.HIGH,
                    source=self.name,
                    fingerprint=fp,
                )
            )

        return findings
