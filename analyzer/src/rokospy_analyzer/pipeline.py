"""Core Static & Security Analysis Pipeline Orchestrator."""

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from rokospy_analyzer.acquisition.workspace import ManagedWorkspace
from rokospy_analyzer.ai.base import AIProvider
from rokospy_analyzer.ai.service import AIEnrichmentService
from rokospy_analyzer.discovery.detector import ProjectDetector
from rokospy_analyzer.models.discovery import ProjectDiscovery
from rokospy_analyzer.models.finding import (
    CategoryEnum,
    SeverityEnum,
    NormalizedFinding,
)
from rokospy_analyzer.models.report import (
    ScannerStatusEnum,
    ScannerExecutionResult,
    ProjectMetadata,
    AnalysisExecutionInfo,
    SeveritySummary,
    CategorySummary,
    AnalysisReport,
)
from rokospy_analyzer.normalization.deduplicator import FindingDeduplicator
from rokospy_analyzer.scanners import get_all_scanners
from rokospy_analyzer.scoring.engine import ScoringEngine
from rokospy_analyzer.security.redactor import SecretRedactor
from rokospy_analyzer.intelligence.structure_analyzer import StructureAnalyzer
from rokospy_analyzer.intelligence.coverage_calculator import CoverageCalculator



class AnalyzerPipeline:
    """Coordinates repository acquisition, inspection, static/security scanning, normalization, AI enrichment, and scoring."""

    @classmethod
    def analyze(cls, target_input: str, ai_provider: Optional[AIProvider] = None) -> AnalysisReport:
        """
        Executes the complete Phase 1 + Phase 2 + Phase 3 analysis pipeline on a Git URL, ZIP file, or local path.
        """
        start_time = time.time()
        start_iso = datetime.now(timezone.utc).isoformat()

        with ManagedWorkspace(target_input) as (workspace_path, source_type, project_name):
            # 1. Project Discovery & Language Detection
            discovery = ProjectDetector.inspect(workspace_path, project_name, source_type)

            all_raw_findings: List[NormalizedFinding] = []
            scanner_results: List[ScannerExecutionResult] = []

            # 2. Execute Scanner Suite
            scanners = get_all_scanners()
            for scanner in scanners:
                scanner_start = time.time()

                if not scanner.is_applicable(discovery):
                    scanner_results.append(
                        ScannerExecutionResult(
                            scanner=scanner.name,
                            status=ScannerStatusEnum.SKIPPED,
                            findings_count=0,
                            duration_ms=0,
                            error_message="Not applicable for detected languages/manifests",
                        )
                    )
                    continue

                if not scanner.is_available():
                    scanner_results.append(
                        ScannerExecutionResult(
                            scanner=scanner.name,
                            status=ScannerStatusEnum.UNAVAILABLE,
                            findings_count=0,
                            duration_ms=0,
                            error_message="Scanner binary or tool not available in PATH",
                        )
                    )
                    continue

                try:
                    status, findings, error_msg = scanner.run(workspace_path, discovery)
                    duration_ms = int((time.time() - scanner_start) * 1000)

                    scanner_results.append(
                        ScannerExecutionResult(
                            scanner=scanner.name,
                            status=status,
                            findings_count=len(findings),
                            duration_ms=duration_ms,
                            error_message=error_msg,
                        )
                    )
                    all_raw_findings.extend(findings)

                except Exception as e:
                    duration_ms = int((time.time() - scanner_start) * 1000)
                    scanner_results.append(
                        ScannerExecutionResult(
                            scanner=scanner.name,
                            status=ScannerStatusEnum.FAILED,
                            findings_count=0,
                            duration_ms=duration_ms,
                            error_message=f"Unhandled scanner exception: {str(e)}",
                        )
                    )

            # 3. Global Secret Redaction & Sanitization Pass
            for finding in all_raw_findings:
                finding.title = SecretRedactor.redact(finding.title)
                finding.message = SecretRedactor.redact(finding.message)
                finding.evidence = SecretRedactor.redact(finding.evidence)

            # 4. Deduplication & Deterministic Ordering
            deduped_findings = FindingDeduplicator.deduplicate(all_raw_findings)

            # 5. Summaries calculation (based strictly on detector evidence)
            severity_summary = SeveritySummary(
                critical=sum(1 for f in deduped_findings if f.severity == SeverityEnum.CRITICAL),
                high=sum(1 for f in deduped_findings if f.severity == SeverityEnum.HIGH),
                medium=sum(1 for f in deduped_findings if f.severity == SeverityEnum.MEDIUM),
                low=sum(1 for f in deduped_findings if f.severity == SeverityEnum.LOW),
                info=sum(1 for f in deduped_findings if f.severity == SeverityEnum.INFO),
            )

            category_summary = CategorySummary(
                bug=sum(1 for f in deduped_findings if f.category == CategoryEnum.BUG),
                security=sum(1 for f in deduped_findings if f.category == CategoryEnum.SECURITY),
                performance=sum(1 for f in deduped_findings if f.category == CategoryEnum.PERFORMANCE),
                quality=sum(1 for f in deduped_findings if f.category == CategoryEnum.QUALITY),
                missing_essential=sum(1 for f in deduped_findings if f.category == CategoryEnum.MISSING_ESSENTIAL),
                architecture=sum(1 for f in deduped_findings if f.category == CategoryEnum.ARCHITECTURE),
            )

            # 6. AI Intelligence & Enrichment Layer (Phase 2)
            ai_service = AIEnrichmentService(provider=ai_provider)
            enriched_findings, ai_summary = ai_service.enrich_findings(
                deduped_findings, workspace_path, discovery
            )

            # 7. Deterministic Scoring Engine (Phase 3)
            project_score = ScoringEngine.evaluate(deduped_findings)

            # 8. Project Intelligence & Coverage Telemetry (Phase 7.5)
            intelligence = StructureAnalyzer.analyze_workspace(
                workspace_path, discovery.project_name, discovery.source_type
            )
            successful_scanners = [
                r.scanner for r in scanner_results if r.status == ScannerStatusEnum.SUCCESS
            ]
            coverage = CoverageCalculator.calculate(intelligence, successful_scanners)

            total_duration_ms = int((time.time() - start_time) * 1000)

            target_url = target_input if (target_input.startswith("http://") or target_input.startswith("https://") or target_input.startswith("git@")) else None

            project_meta = ProjectMetadata(
                name=discovery.project_name,
                source_type=discovery.source_type,
                languages=discovery.detected_languages,
                manifests=discovery.manifests_found,
                target_url=target_url,
            )

            analysis_info = AnalysisExecutionInfo(
                started_at=start_iso,
                duration_ms=total_duration_ms,
                files_analyzed=discovery.total_file_count,
            )

            return AnalysisReport(
                schema_version="1.0",
                project=project_meta,
                analysis=analysis_info,
                scanners=scanner_results,
                findings=enriched_findings,
                summary=severity_summary,
                category_summary=category_summary,
                ai_summary=ai_summary,
                score=project_score,
                coverage=coverage,
                intelligence=intelligence,
            )

