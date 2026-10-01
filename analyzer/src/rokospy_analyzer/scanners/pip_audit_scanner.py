"""pip-audit Scanner adapter for Python dependency vulnerability analysis."""

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


class PipAuditScanner(BaseScanner):
    """Adapter for pip-audit analyzing Python dependency CVEs."""

    @property
    def name(self) -> str:
        return "pip-audit"

    @property
    def supported_languages(self) -> List[str]:
        return ["Python"]

    def is_available(self) -> bool:
        return shutil.which("pip-audit") is not None

    def is_applicable(self, discovery: ProjectDiscovery) -> bool:
        return "requirements.txt" in discovery.manifests_found

    def run(
        self, workspace_path: Path, discovery: ProjectDiscovery
    ) -> Tuple[ScannerStatusEnum, List[NormalizedFinding], Optional[str]]:
        req_file = workspace_path / "requirements.txt"
        if not req_file.exists():
            return ScannerStatusEnum.SKIPPED, [], "requirements.txt not found"

        if not self.is_available():
            return (
                ScannerStatusEnum.UNAVAILABLE,
                [],
                "pip-audit binary is not installed in system PATH (install with 'pip install pip-audit')",
            )

        cmd = [
            "pip-audit",
            "-r", "requirements.txt",
            "-f", "json",
            "--desc",
        ]

        retcode, stdout, stderr = self._execute_subprocess(cmd, workspace_path)

        if not stdout.strip() and retcode not in {0, 1}:
            return ScannerStatusEnum.FAILED, [], f"pip-audit execution failed: {stderr}"

        try:
            data = json.loads(stdout) if stdout.strip() else {"dependencies": []}
        except json.JSONDecodeError as e:
            return ScannerStatusEnum.FAILED, [], f"Failed to parse pip-audit JSON: {str(e)}"

        findings = self._normalize_pip_audit(data)
        return ScannerStatusEnum.SUCCESS, findings, None

    def _normalize_pip_audit(self, data: dict) -> List[NormalizedFinding]:
        findings: List[NormalizedFinding] = []
        deps = data.get("dependencies", [])

        for dep in deps:
            pkg_name = dep.get("name", "unknown")
            installed_ver = dep.get("version", "")
            vulns = dep.get("vulns", [])

            for vuln in vulns:
                vuln_id = vuln.get("id", "CVE-UNKNOWN")
                description = vuln.get("description", "Known dependency vulnerability")
                fix_versions = vuln.get("fix_versions", [])

                title = f"Vulnerable Python Package: {pkg_name} ({vuln_id})"
                fix_text = f"Upgrade to: {', '.join(fix_versions)}" if fix_versions else "No fix version reported"
                message = f"{description}\n{fix_text}"
                evidence = f"Package: {pkg_name} == {installed_ver}\nVulnerability: {vuln_id}\nFix: {fix_text}"

                fp = generate_finding_fingerprint(
                    scanner=self.name,
                    rule_id=vuln_id,
                    file_path="requirements.txt",
                    line=1,
                    title=title,
                )

                findings.append(
                    NormalizedFinding(
                        id=str(uuid.uuid4()),
                        title=title,
                        category=CategoryEnum.SECURITY,
                        severity=SeverityEnum.HIGH,
                        file="requirements.txt",
                        line=1,
                        column=1,
                        rule_id=f"pip-audit-{vuln_id}",
                        scanner=self.name,
                        message=SecretRedactor.redact(message),
                        evidence=SecretRedactor.redact(evidence),
                        confidence=ConfidenceEnum.HIGH,
                        source=self.name,
                        fingerprint=fp,
                    )
                )

        return findings
