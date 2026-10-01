"""Terminal formatting and reporting presentation for Rokospy Analyzer."""

from typing import List
from rokospy_analyzer.models.finding import SeverityEnum, NormalizedFinding
from rokospy_analyzer.models.report import AnalysisReport, ScannerStatusEnum


class TerminalFormatter:
    """Renders high-density, minimal cybersecurity terminal reports (ASCII compatible)."""

    @classmethod
    def format_report(cls, report: AnalysisReport) -> str:
        lines: List[str] = []
        divider = "=" * 70
        sub_divider = "-" * 70

        lines.append(divider)
        lines.append("  Dr.RopoSky -- STATIC & CYBERSECURITY AUDIT REPORT")
        lines.append(divider)

        # 1. Project Info & Overall Score
        lines.append(f"  Project:    {report.project.name} ({report.project.source_type})")
        lines.append(f"  Languages:  {', '.join(report.project.languages) or 'None detected'}")
        lines.append(f"  Manifests:  {', '.join(report.project.manifests) or 'None'}")
        lines.append(f"  Files:      {report.analysis.files_analyzed} analyzed in {report.analysis.duration_ms}ms")
        
        # AI Status Callout
        if report.ai_summary:
            ai_s = report.ai_summary
            ai_status_str = ai_s.status.value if hasattr(ai_s.status, "value") else str(ai_s.status)
            ai_detail = f"({ai_s.enriched_count} enriched, model: {ai_s.model_used or 'n/a'})" if ai_status_str == "success" else f"({ai_s.error_message or ai_status_str})"
            lines.append(f"  AI Layer:   [{ai_status_str.upper()}] {ai_detail}")

        lines.append(sub_divider)

        # 2. Deterministic Project Score (Phase 3)
        if report.score:
            sc = report.score
            lines.append(f"  PROJECT HEALTH SCORE:  [ {sc.overall:3d} / 100 ]  --  {sc.rating_band.upper()}")
            lines.append(f"    Security:     {sc.security:3d}/100    Reliability:  {sc.reliability:3d}/100    Code Quality: {sc.code_quality:3d}/100")
            lines.append(f"    Performance:  {sc.performance:3d}/100    Architecture: {sc.architecture:3d}/100    Completeness: {sc.completeness:3d}/100")
            lines.append(sub_divider)

        # 3. Scanner Statuses
        lines.append("  SCANNERS EXECUTED:")
        for sc in report.scanners:
            status_str = sc.status.value if hasattr(sc.status, "value") else str(sc.status)
            is_success = status_str == "success"
            is_skipped = status_str == "skipped"

            status_icon = "[+]" if is_success else ("[o]" if is_skipped else "[x]")
            status_text = status_str.upper()
            detail = f"({sc.findings_count} findings, {sc.duration_ms}ms)" if is_success else f"({sc.error_message or 'n/a'})"
            lines.append(f"    {status_icon} {sc.scanner:<24} {status_text:<12} {detail}")
        lines.append(sub_divider)

        # 4. Severity & Category Summary
        s = report.summary
        c = report.category_summary
        lines.append("  FINDINGS SUMMARY:")
        lines.append(f"    Critical: {s.critical:<4}  High: {s.high:<4}  Medium: {s.medium:<4}  Low: {s.low:<4}  Info: {s.info:<4}")
        lines.append(f"    Security: {c.security:<4}  Bugs: {c.bug:<4}  Quality: {c.quality:<4}  Perf: {c.performance:<4}  Essentials: {c.missing_essential:<4}")
        lines.append(sub_divider)

        # 5. Critical & High Findings Callout with AI Enrichment
        high_severity_findings = [
            f for f in report.findings
            if (f.severity.value if hasattr(f.severity, "value") else str(f.severity)).lower() in {"critical", "high"}
        ]
        if high_severity_findings:
            lines.append("  CRITICAL / HIGH SECURITY FINDINGS:")
            for idx, f in enumerate(high_severity_findings, start=1):
                sev_str = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
                sev_tag = f"[{sev_str.upper()}]"
                loc = f"{f.file}:{f.line}" if f.line > 0 else f.file
                lines.append(f"    {idx}. {sev_tag:<10} {f.title}")
                lines.append(f"       Location: {loc} (Scanner: {f.scanner})")
                lines.append(f"       Details:  {f.message}")

                # AI Enrichment details if present
                enrichment = getattr(f, "enrichment", None)
                if enrichment and isinstance(enrichment, dict):
                    why = enrichment.get("why_it_matters")
                    fix_steps = enrichment.get("fix_steps", [])
                    if why:
                        lines.append(f"       Why It Matters (AI): {why}")
                    if fix_steps:
                        lines.append("       Remediation Steps (AI):")
                        for step_i, step in enumerate(fix_steps, start=1):
                            lines.append(f"         {step_i}. {step}")
                elif enrichment and hasattr(enrichment, "why_it_matters"):
                    if enrichment.why_it_matters:
                        lines.append(f"       Why It Matters (AI): {enrichment.why_it_matters}")
                    if enrichment.fix_steps:
                        lines.append("       Remediation Steps (AI):")
                        for step_i, step in enumerate(enrichment.fix_steps, start=1):
                            lines.append(f"         {step_i}. {step}")

                if f.evidence:
                    lines.append("       Evidence:")
                    for ev_line in f.evidence.splitlines()[:5]:
                        lines.append(f"         {ev_line}")
                lines.append("")
            lines.append(sub_divider)

        # 6. All Findings List
        lines.append(f"  TOTAL NORMALIZED FINDINGS ({len(report.findings)}):")
        for idx, f in enumerate(report.findings, start=1):
            sev_str = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            cat_str = f.category.value if hasattr(f.category, "value") else str(f.category)
            loc = f"{f.file}:{f.line}" if f.line > 0 else f.file
            lines.append(f"    {idx:2d}. [{sev_str.upper():<8}] [{cat_str:<12}] {f.title}")
            lines.append(f"        Location: {loc} | Rule: {f.rule_id} | Scanner: {f.scanner}")

        lines.append(divider)
        return "\n".join(lines)
