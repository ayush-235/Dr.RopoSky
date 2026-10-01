"""Deterministic Comparison Engine for Phase 7 Re-scan & Progress Tracking."""

import hashlib
import re
from typing import Dict, List, Set, Tuple
from rokospy_analyzer.models.finding import NormalizedFinding
from rokospy_analyzer.models.report import AnalysisReport
from app.schemas.comparison import (
    ComparisonReport,
    ComparisonSummary,
    FindingChangeStatus,
    FindingComparisonItem,
    PillarsDelta,
    ScoreDelta,
)


class ComparisonEngine:
    """Performs pure mathematical, deterministic comparison between two AnalysisReports."""

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize file path for stable cross-platform matching."""
        if not path:
            return ""
        # Convert slashes and lowercase for stable comparison
        cleaned = path.replace("\\", "/").strip().lower()
        if cleaned.startswith("./"):
            cleaned = cleaned[2:]
        return cleaned

    @classmethod
    def _create_stable_signature(cls, finding: NormalizedFinding) -> str:
        """
        Creates a stable finding identity that survives harmless line number movement.
        Combines scanner, rule_id (or title if rule_id missing), category, and normalized file path.
        """
        file_path = getattr(finding, "file", None) or getattr(finding, "file_path", "")
        norm_path = cls._normalize_path(file_path)
        rule_or_title = (finding.rule_id or finding.title or "").strip().lower()
        scanner = (finding.scanner or "").strip().lower()
        category = (finding.category.value if hasattr(finding.category, "value") else str(finding.category)).lower()

        # Extract core alphanumeric tokens from evidence/title to match underlying code signature
        evidence_content = (finding.evidence or finding.title or "").strip().lower()
        evidence_tokens = re.sub(r"\s+", " ", evidence_content)[:80]

        raw_id = f"{scanner}::{category}::{rule_or_title}::{norm_path}::{evidence_tokens}"
        return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()


    @classmethod
    def compare_reports(
        cls, previous_report: AnalysisReport, current_report: AnalysisReport
    ) -> ComparisonReport:
        """
        Deterministically compares two reports and categorizes findings into
        FIXED, NEW, REMAINING, and CHANGED. Calculates exact score deltas.
        """
        prev_findings = previous_report.findings or []
        curr_findings = current_report.findings or []

        # Map signatures to findings
        prev_map: Dict[str, NormalizedFinding] = {}
        for f in prev_findings:
            sig = cls._create_stable_signature(f)
            prev_map[sig] = f

        curr_map: Dict[str, NormalizedFinding] = {}
        for f in curr_findings:
            sig = cls._create_stable_signature(f)
            curr_map[sig] = f

        fixed_findings: List[NormalizedFinding] = []
        new_findings: List[NormalizedFinding] = []
        remaining_findings: List[NormalizedFinding] = []
        changed_findings: List[FindingComparisonItem] = []

        # Find FIXED findings (in prev, not in curr)
        for sig, prev_f in prev_map.items():
            if sig not in curr_map:
                fixed_findings.append(prev_f)

        # Find NEW and REMAINING / CHANGED findings
        for sig, curr_f in curr_map.items():
            if sig not in prev_map:
                new_findings.append(curr_f)
            else:
                prev_f = prev_map[sig]
                # Check for meaningful changes (severity changed or line changed significantly)
                prev_sev = prev_f.severity.value if hasattr(prev_f.severity, "value") else str(prev_f.severity)
                curr_sev = curr_f.severity.value if hasattr(curr_f.severity, "value") else str(curr_f.severity)

                if prev_sev != curr_sev:
                    changed_findings.append(
                        FindingComparisonItem(
                            status=FindingChangeStatus.CHANGED,
                            finding=curr_f,
                            previous_finding=prev_f,
                            change_details=f"Severity changed from {prev_sev.upper()} to {curr_sev.upper()}",
                        )
                    )
                else:
                    remaining_findings.append(curr_f)

        # Calculate Score Deltas
        prev_score = previous_report.score
        curr_score = current_report.score

        prev_overall = prev_score.overall if prev_score else 0
        curr_overall = curr_score.overall if curr_score else 0
        overall_delta_val = curr_overall - prev_overall

        overall_delta = ScoreDelta(
            previous=prev_overall,
            current=curr_overall,
            delta=overall_delta_val,
        )

        def calc_pillar_delta(key: str) -> ScoreDelta:
            p_val = getattr(prev_score, key, 100) if prev_score else 100
            c_val = getattr(curr_score, key, 100) if curr_score else 100
            return ScoreDelta(previous=p_val, current=c_val, delta=c_val - p_val)

        pillars_delta = PillarsDelta(
            security=calc_pillar_delta("security"),
            reliability=calc_pillar_delta("reliability"),
            code_quality=calc_pillar_delta("code_quality"),
            performance=calc_pillar_delta("performance"),
            architecture=calc_pillar_delta("architecture"),
            completeness=calc_pillar_delta("completeness"),
        )

        verdict = (
            "improved"
            if overall_delta_val > 0
            else "regressed"
            if overall_delta_val < 0
            else "unchanged"
        )

        summary = ComparisonSummary(
            fixed_count=len(fixed_findings),
            new_count=len(new_findings),
            remaining_count=len(remaining_findings),
            changed_count=len(changed_findings),
            overall_delta=overall_delta_val,
            verdict=verdict,
        )

        return ComparisonReport(
            schema_version="1.0",
            summary=summary,
            overall=overall_delta,
            pillars=pillars_delta,
            fixed_findings=fixed_findings,
            new_findings=new_findings,
            remaining_findings=remaining_findings,
            changed_findings=changed_findings,
        )
