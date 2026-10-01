"""ESLint Scanner adapter for JavaScript/TypeScript lint and security rule scanning."""

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


class ESLintScanner(BaseScanner):
    """Adapter for ESLint static code analysis."""

    @property
    def name(self) -> str:
        return "eslint"

    @property
    def supported_languages(self) -> List[str]:
        return ["JavaScript", "TypeScript"]

    def is_available(self) -> bool:
        return shutil.which("eslint") is not None

    def is_applicable(self, discovery: ProjectDiscovery) -> bool:
        return bool(set(discovery.detected_languages).intersection({"JavaScript", "TypeScript"}))

    def run(
        self, workspace_path: Path, discovery: ProjectDiscovery
    ) -> Tuple[ScannerStatusEnum, List[NormalizedFinding], Optional[str]]:
        if not self.is_available():
            return (
                ScannerStatusEnum.UNAVAILABLE,
                [],
                "ESLint binary is not installed in system PATH (install with 'npm install -g eslint')",
            )

        cmd = [
            "eslint",
            ".",
            "--format", "json",
            "--ignore-pattern", "node_modules/",
            "--ignore-pattern", "dist/",
            "--ignore-pattern", "build/",
            "--ignore-pattern", ".next/",
        ]

        retcode, stdout, stderr = self._execute_subprocess(cmd, workspace_path)

        if not stdout.strip() and retcode not in {0, 1}:
            return ScannerStatusEnum.FAILED, [], f"ESLint execution failed: {stderr}"

        try:
            data = json.loads(stdout) if stdout.strip() else []
        except json.JSONDecodeError as e:
            return ScannerStatusEnum.FAILED, [], f"Failed to parse ESLint JSON output: {str(e)}"

        findings = self._normalize_eslint(data, workspace_path)
        return ScannerStatusEnum.SUCCESS, findings, None

    def _normalize_eslint(self, data: list, workspace_path: Path) -> List[NormalizedFinding]:
        findings: List[NormalizedFinding] = []

        for file_report in data:
            raw_path = file_report.get("filePath", "")
            try:
                rel_file = str(Path(raw_path).relative_to(workspace_path)).replace("\\", "/")
            except Exception:
                rel_file = str(Path(raw_path)).replace("\\", "/")

            messages = file_report.get("messages", [])
            for msg_item in messages:
                rule_id = msg_item.get("ruleId", "eslint-rule") or "syntax-error"
                message = msg_item.get("message", "Lint issue detected")
                line_num = int(msg_item.get("line", 1))
                col_num = int(msg_item.get("column", 1))
                raw_severity = msg_item.get("severity", 1)  # 1 = warning, 2 = error

                category = CategoryEnum.QUALITY
                severity = SeverityEnum.LOW if raw_severity == 1 else SeverityEnum.MEDIUM

                if "security" in rule_id.lower() or "no-eval" in rule_id or "no-implied-eval" in rule_id:
                    category = CategoryEnum.SECURITY
                    severity = SeverityEnum.HIGH
                elif "no-undef" in rule_id or "no-unused-vars" in rule_id or "syntax" in rule_id:
                    category = CategoryEnum.BUG
                    severity = SeverityEnum.HIGH if raw_severity == 2 else SeverityEnum.MEDIUM

                title = f"JS/TS {category.title()}: {message.splitlines()[0]}"
                sanitized_message = SecretRedactor.redact(message)

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
                        category=category,
                        severity=severity,
                        file=rel_file,
                        line=line_num,
                        column=col_num,
                        rule_id=f"eslint-{rule_id}",
                        scanner=self.name,
                        message=sanitized_message,
                        evidence=f"Line {line_num}:{col_num} - {sanitized_message}",
                        confidence=ConfidenceEnum.HIGH,
                        source=self.name,
                        fingerprint=fp,
                    )
                )

        return findings
