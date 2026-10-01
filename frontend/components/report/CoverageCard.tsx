"use client";

import React, { useState } from "react";
import { AnalysisCoverage, ProjectIntelligence } from "@/types/report";
import { ShieldCheck, Layers, FileCode, CheckCircle2, HelpCircle, ChevronDown, ChevronUp, Lock, Terminal, Activity } from "lucide-react";

interface CoverageCardProps {
  coverage?: AnalysisCoverage | null;
  intelligence?: ProjectIntelligence | null;
}

export const CoverageCard: React.FC<CoverageCardProps> = ({
  coverage,
  intelligence,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!coverage) return null;

  return (
    <div className="w-full p-6 rounded-xl border border-border bg-surface/60 mb-6 backdrop-blur-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/60 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Activity className="w-4 h-4 text-primary" />
            <h3 className="text-xs font-mono text-text-secondary uppercase tracking-wider">
              Static Analysis Coverage & Project Intelligence
            </h3>
          </div>
          <p className="text-xs font-mono text-text-muted">
            {coverage.evaluation_summary}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex flex-col items-end">
            <span className="text-[10px] font-mono text-text-muted uppercase">Scope Coverage</span>
            <span className="text-xl font-bold font-mono text-primary">
              {coverage.overall_coverage_pct}%
            </span>
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-3 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface border border-border text-xs font-mono text-text-primary transition-all flex items-center gap-1.5"
          >
            <span>{isExpanded ? "Hide Details" : "Inspect Coverage"}</span>
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Quick Intelligence Badges */}
      {intelligence && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
          <div className="p-3 rounded-lg bg-surface border border-border">
            <span className="text-[10px] font-mono text-text-muted block uppercase">Project Type</span>
            <span className="text-xs font-mono font-semibold text-text-primary uppercase">
              {intelligence.project_type.replace("_", " ")}
            </span>
          </div>

          <div className="p-3 rounded-lg bg-surface border border-border">
            <span className="text-[10px] font-mono text-text-muted block uppercase">Endpoints Discovered</span>
            <span className="text-xs font-mono font-semibold text-text-primary">
              {intelligence.routes_detected?.length ?? 0} API Routes
            </span>
          </div>

          <div className="p-3 rounded-lg bg-surface border border-border">
            <span className="text-[10px] font-mono text-text-muted block uppercase">Lockfile Status</span>
            <span className={`text-xs font-mono font-semibold ${intelligence.has_lockfile ? "text-emerald-400" : "text-amber-400"}`}>
              {intelligence.has_lockfile ? "Deterministic Lockfile" : "Missing Lockfile"}
            </span>
          </div>

          <div className="p-3 rounded-lg bg-surface border border-border">
            <span className="text-[10px] font-mono text-text-muted block uppercase">Automated Tests</span>
            <span className={`text-xs font-mono font-semibold ${intelligence.has_tests ? "text-emerald-400" : "text-amber-400"}`}>
              {intelligence.has_tests ? `${intelligence.test_files_count} Test Files` : "No Tests Detected"}
            </span>
          </div>
        </div>
      )}

      {/* Expanded Breakdown per Pillar */}
      {isExpanded && (
        <div className="mt-6 pt-4 border-t border-border/60 grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(coverage.pillars).map(([key, pillar]) => (
            <div key={key} className="p-4 rounded-lg bg-surface border border-border/80 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono font-semibold text-text-primary uppercase">
                    {pillar.pillar.replace("_", " ")}
                  </span>
                  <span className="text-xs font-mono font-bold text-primary">
                    {pillar.coverage_pct}%
                  </span>
                </div>

                <div className="space-y-2 mt-3">
                  <div>
                    <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1 mb-1">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Verified Properties</span>
                    </span>
                    <ul className="text-[11px] font-mono text-text-secondary space-y-0.5 pl-4 list-disc">
                      {pillar.verifiable_aspects.map((aspect, i) => (
                        <li key={i}>{aspect}</li>
                      ))}
                    </ul>
                  </div>

                  {pillar.unverified_aspects.length > 0 && (
                    <div className="mt-2">
                      <span className="text-[10px] font-mono text-zinc-400 flex items-center gap-1 mb-1">
                        <HelpCircle className="w-3 h-3" />
                        <span>Unverified / Out of Scope</span>
                      </span>
                      <ul className="text-[11px] font-mono text-text-muted space-y-0.5 pl-4 list-disc">
                        {pillar.unverified_aspects.map((aspect, i) => (
                          <li key={i}>{aspect}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
