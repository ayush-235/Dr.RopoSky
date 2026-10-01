"""AI Enrichment Service orchestrating context extraction, provider calls, and result attachment."""

import time
from pathlib import Path
from typing import List, Optional, Tuple
from rokospy_analyzer.ai.base import AIProvider
from rokospy_analyzer.ai.context_extractor import ContextExtractor
from rokospy_analyzer.ai.gemini_provider import GeminiProvider
from rokospy_analyzer.ai.models import (
    AIExecutionSummary,
    AIStatusEnum,
    AIFindingEnrichment,
    AIConfidenceEnum,
)
from rokospy_analyzer.config import config
from rokospy_analyzer.models.discovery import ProjectDiscovery
from rokospy_analyzer.models.finding import NormalizedFinding, SeverityEnum


class AIEnrichmentService:
    """Service that enriches normalized static findings with AI explanations while preserving evidence."""

    def __init__(self, provider: Optional[AIProvider] = None):
        self.provider = provider or GeminiProvider()

    def enrich_findings(
        self,
        findings: List[NormalizedFinding],
        workspace_path: Path,
        discovery: ProjectDiscovery,
    ) -> Tuple[List[NormalizedFinding], AIExecutionSummary]:
        """
        Iterates over prioritized findings and attaches AI explanations.
        Preserves original scanner findings completely even if AI fails or is unavailable.
        """
        start_time = time.time()
        enriched_count = 0
        failed_count = 0

        if not self.provider.is_available():
            duration_ms = int((time.time() - start_time) * 1000)
            summary = AIExecutionSummary(
                status=AIStatusEnum.UNAVAILABLE,
                enriched_count=0,
                failed_count=0,
                duration_ms=duration_ms,
                model_used=getattr(self.provider, "model_name", None),
                error_message="AI provider is not configured or unavailable",
            )
            # Attach default fallback message to findings
            for f in findings:
                f.enrichment = AIFindingEnrichment(
                    why_it_matters=f"Static finding reported by {f.scanner} ({f.rule_id}).",
                    impact="AI enrichment unavailable in current environment.",
                    fix_steps=["Refer to detector documentation for remediation."],
                    code_before=f.evidence,
                    code_after="",
                    confidence=AIConfidenceEnum.LOW,
                    status=AIStatusEnum.UNAVAILABLE,
                    error_message="AI provider not configured",
                )
            return findings, summary

        # Prioritize findings: Critical > High > Medium > Low > Info
        sorted_indices = sorted(
            range(len(findings)),
            key=lambda idx: (
                0 if findings[idx].severity == SeverityEnum.CRITICAL
                else 1 if findings[idx].severity == SeverityEnum.HIGH
                else 2 if findings[idx].severity == SeverityEnum.MEDIUM
                else 3
            )
        )

        limit = min(len(findings), config.MAX_AI_FINDINGS_PER_SCAN)
        indices_to_enrich = set(sorted_indices[:limit])

        for idx, finding in enumerate(findings):
            if idx not in indices_to_enrich:
                # Mark as skipped due to limit
                finding.enrichment = AIFindingEnrichment(
                    why_it_matters=f"Static finding reported by {finding.scanner} ({finding.rule_id}).",
                    impact="Skipped due to per-scan AI enrichment budget limits.",
                    fix_steps=["Inspect the affected source file directly."],
                    code_before=finding.evidence,
                    code_after="",
                    confidence=AIConfidenceEnum.LOW,
                    status=AIStatusEnum.SKIPPED,
                    error_message="Exceeded max AI findings per scan limit",
                )
                continue

            # Extract sanitized context
            context_data = ContextExtractor.extract_context(finding, workspace_path, discovery)

            # Call AI provider
            enrichment = self.provider.enrich_finding(context_data)
            finding.enrichment = enrichment

            if enrichment.status == AIStatusEnum.SUCCESS:
                enriched_count += 1
            else:
                failed_count += 1

        duration_ms = int((time.time() - start_time) * 1000)
        overall_status = AIStatusEnum.SUCCESS if enriched_count > 0 else (
            AIStatusEnum.FAILED if failed_count > 0 else AIStatusEnum.SKIPPED
        )

        summary = AIExecutionSummary(
            status=overall_status,
            enriched_count=enriched_count,
            failed_count=failed_count,
            duration_ms=duration_ms,
            model_used=getattr(self.provider, "model_name", None),
            error_message=None if enriched_count > 0 else "All AI enrichments failed or were skipped",
        )

        return findings, summary
