"use client";

import React from "react";
import { NormalizedFinding } from "@/types/report";

interface SecuritySeverityBreakdownProps {
  findings: NormalizedFinding[];
}

export const SecuritySeverityBreakdown: React.FC<SecuritySeverityBreakdownProps> = ({
  findings,
}) => {
  // Compute counts strictly from security-relevant findings
  const critical = findings.filter((f) => f.severity === "critical").length;
  const high = findings.filter((f) => f.severity === "high").length;
  const medium = findings.filter((f) => f.severity === "medium").length;
  const low = findings.filter((f) => f.severity === "low").length;
  const info = findings.filter((f) => f.severity === "info").length;
  const total = findings.length;

  return (
    <div className="p-5 rounded-xl border border-border bg-surface/60 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs font-mono font-bold text-text-primary uppercase tracking-wider">
          Security Severity Triage ({total} Vulnerabilities)
        </h3>
        <span className="text-[11px] font-mono text-text-muted">
          Prioritized by threat severity
        </span>
      </div>

      {/* Stacked Ratio Bar */}
      <div className="w-full h-3 rounded-full bg-surface-elevated overflow-hidden flex mb-4 border border-border-subtle">
        {critical > 0 && (
          <div
            style={{ width: `${(critical / total) * 100}%` }}
            className="bg-red-500 h-full transition-all"
            title={`Critical: ${critical}`}
          />
        )}
        {high > 0 && (
          <div
            style={{ width: `${(high / total) * 100}%` }}
            className="bg-orange-500 h-full transition-all"
            title={`High: ${high}`}
          />
        )}
        {medium > 0 && (
          <div
            style={{ width: `${(medium / total) * 100}%` }}
            className="bg-amber-500 h-full transition-all"
            title={`Medium: ${medium}`}
          />
        )}
        {low > 0 && (
          <div
            style={{ width: `${(low / total) * 100}%` }}
            className="bg-blue-500 h-full transition-all"
            title={`Low: ${low}`}
          />
        )}
        {info > 0 && (
          <div
            style={{ width: `${(info / total) * 100}%` }}
            className="bg-zinc-500 h-full transition-all"
            title={`Info: ${info}`}
          />
        )}
        {total === 0 && (
          <div className="bg-emerald-500 h-full w-full opacity-60" />
        )}
      </div>

      {/* Severity Metric Boxes */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="p-3 rounded-lg border border-red-500/20 bg-red-500/5">
          <div className="text-[11px] font-mono text-red-400 font-semibold mb-1">
            CRITICAL
          </div>
          <div className="text-2xl font-bold font-mono text-red-400">
            {critical}
          </div>
          <div className="text-[10px] font-mono text-text-muted">Immediate action</div>
        </div>

        <div className="p-3 rounded-lg border border-orange-500/20 bg-orange-500/5">
          <div className="text-[11px] font-mono text-orange-400 font-semibold mb-1">
            HIGH
          </div>
          <div className="text-2xl font-bold font-mono text-orange-400">
            {high}
          </div>
          <div className="text-[10px] font-mono text-text-muted">High priority</div>
        </div>

        <div className="p-3 rounded-lg border border-amber-500/20 bg-amber-500/5">
          <div className="text-[11px] font-mono text-amber-400 font-semibold mb-1">
            MEDIUM
          </div>
          <div className="text-2xl font-bold font-mono text-amber-400">
            {medium}
          </div>
          <div className="text-[10px] font-mono text-text-muted">Moderate impact</div>
        </div>

        <div className="p-3 rounded-lg border border-blue-500/20 bg-blue-500/5">
          <div className="text-[11px] font-mono text-blue-400 font-semibold mb-1">
            LOW
          </div>
          <div className="text-2xl font-bold font-mono text-blue-400">
            {low}
          </div>
          <div className="text-[10px] font-mono text-text-muted">Low severity</div>
        </div>

        <div className="p-3 rounded-lg border border-zinc-500/20 bg-zinc-500/5">
          <div className="text-[11px] font-mono text-zinc-400 font-semibold mb-1">
            INFO
          </div>
          <div className="text-2xl font-bold font-mono text-zinc-400">
            {info}
          </div>
          <div className="text-[10px] font-mono text-text-muted">Informational</div>
        </div>
      </div>
    </div>
  );
};
