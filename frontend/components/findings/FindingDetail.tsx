"use client";

import React from "react";
import { NormalizedFinding } from "@/types/report";
import { getSeverityStyle, getCategoryLabel, formatScannerName } from "@/lib/utils";
import { CodeViewer } from "../code-viewer/CodeViewer";
import {
  Shield,
  Sparkles,
  FileCode,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Cpu,
  Layers,
  Bug,
} from "lucide-react";

interface FindingDetailProps {
  finding: NormalizedFinding;
  comparisonStatus?: "fixed" | "new" | "remaining" | "changed";
  previousFinding?: NormalizedFinding | null;
  changeDetails?: string | null;
}

export const FindingDetail: React.FC<FindingDetailProps> = ({
  finding,
  comparisonStatus,
  previousFinding,
  changeDetails,
}) => {
  const sevStyle = getSeverityStyle(finding.severity);
  const enrichment = finding.enrichment;
  const filePath = finding.file_path || finding.file || "";
  const lineNum =
    finding.line_number !== undefined && finding.line_number !== null
      ? finding.line_number
      : finding.line !== undefined && finding.line !== null
      ? finding.line
      : null;

  // Guess language from file extension
  const getLanguage = (pathStr: string) => {
    if (!pathStr) return "plaintext";
    const lower = pathStr.toLowerCase();
    if (lower.endsWith(".ts") || lower.endsWith(".tsx")) return "typescript";
    if (lower.endsWith(".js") || lower.endsWith(".jsx")) return "javascript";
    if (lower.endsWith(".py")) return "python";
    if (lower.endsWith(".json")) return "json";
    if (lower.endsWith(".html")) return "html";
    if (lower.endsWith(".css")) return "css";
    if (lower.endsWith(".md")) return "markdown";
    return "plaintext";
  };

  const confidenceValue =
    typeof enrichment?.confidence_score === "number"
      ? `${Math.round(enrichment.confidence_score * 100)}%`
      : typeof (enrichment as any)?.confidence === "number"
      ? `${Math.round((enrichment as any).confidence * 100)}%`
      : (enrichment as any)?.confidence
      ? String((enrichment as any).confidence).toUpperCase()
      : "Standard";

  return (
    <div className="p-6 rounded-xl border border-border bg-surface flex flex-col gap-6 shadow-xl">
      {/* Comparison Delta Status Banner if applicable */}
      {comparisonStatus && (
        <div
          className={`p-3.5 rounded-lg border font-mono text-xs flex flex-wrap items-center justify-between gap-3 ${
            comparisonStatus === "fixed"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              : comparisonStatus === "new"
              ? "bg-rose-500/10 border-rose-500/30 text-rose-400"
              : comparisonStatus === "changed"
              ? "bg-purple-500/10 border-purple-500/30 text-purple-400"
              : "bg-surface-elevated border-border text-text-muted"
          }`}
        >
          <div className="flex items-center gap-2">
            <span className="font-bold uppercase tracking-wider">
              Status: {comparisonStatus.toUpperCase()}
            </span>
            {comparisonStatus === "fixed" && (
              <span className="text-text-primary text-[11px]">
                &bull; Previous Severity: <strong className="uppercase">{(previousFinding?.severity || finding.severity).toUpperCase()}</strong> &rarr; Current: <span className="text-emerald-400 font-bold">Not detected (Resolved)</span>
              </span>
            )}
            {comparisonStatus === "new" && (
              <span className="text-text-primary text-[11px]">
                &bull; Previous: <span className="text-text-muted">Not detected</span> &rarr; Current Severity: <strong className="uppercase text-rose-400">{finding.severity.toUpperCase()}</strong>
              </span>
            )}
            {comparisonStatus === "remaining" && (
              <span className="text-text-primary text-[11px]">
                &bull; Severity: <strong className="uppercase">{finding.severity.toUpperCase()}</strong> (Persisting unresolved across scans)
              </span>
            )}
            {comparisonStatus === "changed" && (
              <span className="text-text-primary text-[11px]">
                &bull; {changeDetails || `Severity changed from ${(previousFinding?.severity || "unknown").toUpperCase()} to ${finding.severity.toUpperCase()}`}
              </span>
            )}
          </div>
        </div>
      )}
      {/* Header */}
      <div>
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <span
            className={`text-xs font-mono font-semibold px-2.5 py-1 rounded-full border uppercase ${sevStyle.badge}`}
          >
            {finding.severity}
          </span>
          <span className="text-xs font-mono px-2.5 py-1 rounded-full border border-border bg-surface-elevated text-text-secondary">
            {getCategoryLabel(finding.category)}
          </span>
          <span className="text-xs font-mono text-text-muted">
            Detected by <strong className="text-text-primary">{formatScannerName(finding.scanner)}</strong>
          </span>
          {finding.rule_id && (
            <span className="text-xs font-mono text-text-muted">
              Rule: <code className="text-primary">{finding.rule_id}</code>
            </span>
          )}
        </div>

        <h2 className="text-lg font-bold font-mono text-text-primary">
          {finding.title}
        </h2>

        <div className="flex items-center gap-2 text-xs font-mono text-text-secondary mt-1.5">
          <FileCode className="w-4 h-4 text-primary" />
          <span>
            {filePath || "Project file"}
            {lineNum ? `:${lineNum}` : ""}
          </span>
        </div>
      </div>

      {/* Message */}
      <div className="p-4 rounded-lg bg-surface-elevated border border-border text-xs sm:text-sm font-mono text-text-primary leading-relaxed">
        {finding.message}
      </div>

      {/* Code Evidence (Sanitized) */}
      {finding.evidence && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono text-text-secondary uppercase tracking-wider">
              Static Code Evidence (Sanitized)
            </span>
            <span className="text-[11px] font-mono text-emerald-400">
              Secrets Redacted
            </span>
          </div>
          <CodeViewer
            code={finding.evidence}
            language={getLanguage(filePath)}
            height="140px"
            highlightLine={lineNum}
          />
        </div>
      )}

      {/* AI Enrichment Section */}
      {enrichment ? (
        <div className="space-y-4 pt-2 border-t border-border">
          {/* AI Badge */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-mono text-accent-violet">
              <Sparkles className="w-4 h-4" />
              <span className="font-semibold uppercase tracking-wider">
                AI Intelligence & Remediation (Gemini)
              </span>
            </div>
            <span className="text-xs font-mono text-text-muted">
              Confidence: {confidenceValue}
            </span>
          </div>

          {/* Why It Matters */}
          {(enrichment.why_it_matters || enrichment.explanation) && (
            <div className="p-4 rounded-lg bg-accent-violet/5 border border-accent-violet/20">
              <h3 className="text-xs font-bold font-mono text-accent-violet uppercase tracking-wider mb-1.5">
                Why It Matters
              </h3>
              <p className="text-xs sm:text-sm font-mono text-text-primary leading-relaxed">
                {enrichment.why_it_matters || enrichment.explanation}
              </p>
            </div>
          )}

          {/* Fix Steps */}
          {enrichment.fix_steps && enrichment.fix_steps.length > 0 && (
            <div>
              <h3 className="text-xs font-bold font-mono text-text-secondary uppercase tracking-wider mb-2">
                Step-by-Step Remediation
              </h3>
              <ol className="space-y-2">
                {enrichment.fix_steps.map((step, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2.5 p-3 rounded-lg bg-surface-elevated border border-border text-xs font-mono text-text-primary"
                  >
                    <span className="w-5 h-5 rounded-full bg-primary/10 border border-primary/30 text-primary flex items-center justify-center shrink-0 font-bold">
                      {idx + 1}
                    </span>
                    <span className="mt-0.5">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Suggested Code Diff */}
          {(enrichment.suggested_code_diff || enrichment.code_after) && (
            <div>
              <h3 className="text-xs font-bold font-mono text-text-secondary uppercase tracking-wider mb-2">
                Suggested Fix Diff
              </h3>
              <CodeViewer
                code={
                  enrichment.suggested_code_diff ||
                  `- ${enrichment.code_before || ""}\n+ ${enrichment.code_after || ""}`
                }
                language="diff"
                height="160px"
              />
            </div>
          )}
        </div>
      ) : (
        <div className="p-3 rounded-lg bg-surface-elevated/40 border border-border text-xs font-mono text-text-muted">
          AI enrichment is disabled or was skipped for this finding.
        </div>
      )}
    </div>
  );
};
