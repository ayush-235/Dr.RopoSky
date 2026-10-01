"""npm audit Scanner adapter for Node.js dependency vulnerability analysis.

Never runs npm install or executes untrusted lifecycle scripts.
Only analyzes existing dependency metadata and lockfiles statically.
"""

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


class NpmAuditScanner(BaseScanner):
    """Adapter for npm audit analyzing lockfile dependency vulnerabilities safely."""

    @property
    def name(self) -> str:
        return "npm-audit"

    @property
    def supported_languages(self) -> List[str]:
        return ["JavaScript", "TypeScript"]

    def is_available(self) -> bool:
        return shutil.which("npm") is not None

    def is_applicable(self, discovery: ProjectDiscovery) -> bool:
        return "package-lock.json" in discovery.manifests_found or "package.json" in discovery.manifests_found

    def run(
        self, workspace_path: Path, discovery: ProjectDiscovery
    ) -> Tuple[ScannerStatusEnum, List[NormalizedFinding], Optional[str]]:
        lockfile_path = workspace_path / "package-lock.json"

        # If lockfile does not exist, check if package.json has dependencies
        if not lockfile_path.exists():
            # Static check on package.json without lockfile
            return self._inspect_package_json(workspace_path)

        if not self.is_available():
            return (
                ScannerStatusEnum.UNAVAILABLE,
                [],
                "npm binary is not installed in system PATH",
            )

        # Execute npm audit strictly on the lockfile without running npm install or scripts
        cmd = [
            "npm",
            "audit",
            "--package-lock-only",
            "--json",
            "--audit-level=low",
        ]

        retcode, stdout, stderr = self._execute_subprocess(cmd, workspace_path)

        if not stdout.strip():
            return ScannerStatusEnum.FAILED, [], f"npm audit produced no output: {stderr}"

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            return ScannerStatusEnum.FAILED, [], f"Failed to parse npm audit JSON: {str(e)}"

        findings = self._normalize_npm_audit(data)
        return ScannerStatusEnum.SUCCESS, findings, None

    def _inspect_package_json(self, workspace_path: Path) -> Tuple[ScannerStatusEnum, List[NormalizedFinding], Optional[str]]:
        """Static inspection when package.json exists but package-lock.json is missing."""
        pkg_file = workspace_path / "package.json"
        if not pkg_file.exists():
            return ScannerStatusEnum.SKIPPED, [], "No package.json present"

        findings: List[NormalizedFinding] = []
        fp = generate_finding_fingerprint(
            scanner=self.name,
            rule_id="missing-package-lock",
            file_path="package.json",
            line=1,
            title="Missing package-lock.json",
        )
        findings.append(
            NormalizedFinding(
                id=str(uuid.uuid4()),
                title="Missing Lockfile (package-lock.json)",
                category=CategoryEnum.QUALITY,
                severity=SeverityEnum.LOW,
                file="package.json",
                line=1,
                column=1,
                rule_id="missing-package-lock",
                scanner=self.name,
                message="Project has a package.json but no package-lock.json. Lockfiles ensure deterministic dependency resolution and reproducible vulnerability scanning.",
                evidence="package.json is present without package-lock.json.",
                confidence=ConfidenceEnum.HIGH,
                source=self.name,
                fingerprint=fp,
            )
        )
        return ScannerStatusEnum.SUCCESS, findings, None

    def _normalize_npm_audit(self, data: dict) -> List[NormalizedFinding]:
        findings: List[NormalizedFinding] = []
        vulnerabilities = data.get("vulnerabilities", {})

        sev_map = {
            "critical": SeverityEnum.CRITICAL,
            "high": SeverityEnum.HIGH,
            "moderate": SeverityEnum.MEDIUM,
            "low": SeverityEnum.LOW,
            "info": SeverityEnum.INFO,
        }

        for pkg_name, details in vulnerabilities.items():
            raw_sev = details.get("severity", "moderate").lower()
            normalized_sev = sev_map.get(raw_sev, SeverityEnum.MEDIUM)
            via = details.get("via", [])

            title_desc = f"Vulnerable Dependency: {pkg_name}"
            advisory_url = ""
            if via and isinstance(via[0], dict):
                title_desc = f"Vulnerability in {pkg_name}: {via[0].get('title', 'Known vulnerability')}"
                advisory_url = via[0].get("url", "")
            elif via and isinstance(via[0], str):
                title_desc = f"Vulnerability in dependency chain: {pkg_name} via {via[0]}"

            message = f"Dependency '{pkg_name}' has a known {raw_sev} vulnerability. {advisory_url}".strip()
            range_info = details.get("range", "")
            fix_available = details.get("fixAvailable", False)

            evidence = f"Package: {pkg_name} (range: {range_info})\nFix available: {fix_available}"

            rule_id = f"npm-vuln-{pkg_name}"
            fp = generate_finding_fingerprint(
                scanner=self.name,
                rule_id=rule_id,
                file_path="package-lock.json",
                line=1,
                title=title_desc,
            )

            findings.append(
                NormalizedFinding(
                    id=str(uuid.uuid4()),
                    title=title_desc,
                    category=CategoryEnum.SECURITY,
                    severity=normalized_sev,
                    file="package-lock.json",
                    line=1,
                    column=1,
                    rule_id=rule_id,
                    scanner=self.name,
                    message=SecretRedactor.redact(message),
                    evidence=SecretRedactor.redact(evidence),
                    confidence=ConfidenceEnum.HIGH,
                    source=self.name,
                    fingerprint=fp,
                )
            )

        return findings
