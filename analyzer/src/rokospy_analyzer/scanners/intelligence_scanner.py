"""Project Intelligence & Architectural Scanner adapter."""

import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from rokospy_analyzer.intelligence.structure_analyzer import StructureAnalyzer
from rokospy_analyzer.intelligence.architecture_analyzer import ArchitectureAnalyzer
from rokospy_analyzer.intelligence.security_analyzer import SecurityAnalyzer
from rokospy_analyzer.models.discovery import ProjectDiscovery
from rokospy_analyzer.models.finding import (
    CategoryEnum,
    SeverityEnum,
    ConfidenceEnum,
    NormalizedFinding,
)
from rokospy_analyzer.models.report import ScannerStatusEnum
from rokospy_analyzer.normalization.fingerprint import FindingFingerprint
from rokospy_analyzer.scanners.base import BaseScanner


class ProjectIntelligenceScanner(BaseScanner):
    """Static scanner analyzing project topology, env docs, lockfiles, God modules, layer boundaries, auth, and security."""

    @property
    def name(self) -> str:
        return "rokospy-project-intelligence"

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

        try:
            # 1. Run Structural Analysis
            intel = StructureAnalyzer.analyze_workspace(
                workspace_path, discovery.project_name, discovery.source_type
            )

            # Check for undocumented environment variables
            if intel.missing_env_vars:
                var_list = ", ".join(intel.missing_env_vars[:5])
                if len(intel.missing_env_vars) > 5:
                    var_list += f" (+{len(intel.missing_env_vars) - 5} more)"

                fp = FindingFingerprint.generate(
                    self.name, "missing-env-documentation", ".env.example", 1, "Undocumented Environment Variables"
                )
                findings.append(
                    NormalizedFinding(
                        id=str(uuid.uuid4()),
                        title=f"Undocumented Environment Variables ({len(intel.missing_env_vars)} vars)",
                        category=CategoryEnum.MISSING_ESSENTIAL,
                        severity=SeverityEnum.LOW,
                        file=".env.example",
                        file_path=".env.example",
                        line=1,
                        line_number=1,
                        column=0,
                        column_number=0,
                        rule_id="missing-env-documentation",
                        scanner=self.name,
                        message=(
                            f"Detected {len(intel.missing_env_vars)} environment variable(s) used in source code "
                            f"({var_list}) that are not documented in .env.example or template files. "
                            "Undocumented environment variables lead to deployment failures and developer onboarding confusion."
                        ),
                        evidence=f"Undocumented variables: {', '.join(intel.missing_env_vars)}",
                        confidence=ConfidenceEnum.HIGH,
                        source=self.name,
                        fingerprint=fp,
                    )
                )

            # Check for missing dependency lockfile
            if intel.direct_dependencies and not intel.has_lockfile:
                target_manifest = discovery.manifests_found[0] if discovery.manifests_found else "dependencies"
                fp = FindingFingerprint.generate(
                    self.name, "missing-dependency-lockfile", target_manifest, 1, "Missing Dependency Lockfile"
                )
                findings.append(
                    NormalizedFinding(
                        id=str(uuid.uuid4()),
                        title="Missing Dependency Lockfile",
                        category=CategoryEnum.QUALITY,
                        severity=SeverityEnum.LOW,
                        file=target_manifest,
                        file_path=target_manifest,
                        line=1,
                        line_number=1,
                        column=0,
                        column_number=0,
                        rule_id="missing-dependency-lockfile",
                        scanner=self.name,
                        message=(
                            f"Project declares direct dependencies ({len(intel.direct_dependencies)} packages) but lacks a "
                            "deterministic lockfile (package-lock.json, pnpm-lock.yaml, yarn.lock, poetry.lock, Pipfile.lock, etc.). "
                            "Without lockfiles, builds are non-reproducible and vulnerable to unintended upstream breakages."
                        ),
                        evidence=f"Declared packages without lockfile: {', '.join(intel.direct_dependencies[:5])}",
                        confidence=ConfidenceEnum.HIGH,
                        source=self.name,
                        fingerprint=fp,
                    )
                )

            # 2. Run Architecture Analysis
            arch_findings = ArchitectureAnalyzer.analyze_workspace(workspace_path)
            findings.extend(arch_findings)

            # 3. Run Static Security & Authorization Analysis (Phase 7.6)
            sec_findings = SecurityAnalyzer.analyze_workspace(workspace_path, intel)
            findings.extend(sec_findings)

            return ScannerStatusEnum.SUCCESS, findings, None

        except Exception as e:
            return ScannerStatusEnum.FAILED, [], f"Project intelligence scanner error: {str(e)}"

