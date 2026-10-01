"use client";

import React from "react";
import { ProjectScore, SeveritySummary } from "@/types/report";
import { getRatingBandColor } from "@/lib/utils";
import { ShieldAlert, AlertTriangle, Info, CheckCircle2, GitCompare } from "lucide-react";

interface OverallScoreCardProps {
  score: ProjectScore;
  summary: SeveritySummary;
  onRescanClick?: () => void;
}

export const OverallScoreCard: React.FC<OverallScoreCardProps> = ({
  score,
  summary,
  onRescanClick,
}) => {
  const bandStyle = getRatingBandColor(score.rating_band);
  const totalFindings =
    summary.critical +
    summary.high +
    summary.medium +
    summary.low +
    summary.info;

  return (
    <div className="w-full grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      {/* Overall Score Box */}
      <div className={`col-span-1 p-6 rounded-xl border ${bandStyle.border} bg-gradient-to-b ${bandStyle.bg} bg-surface/80 flex flex-col justify-between`}>
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-text-secondary uppercase tracking-wider">
            Overall Health Score
          </span>
          <span
            className={`text-xs font-mono font-semibold px-2.5 py-1 rounded-full border ${bandStyle.badge}`}
          >
            {score.rating_band}
          </span>
        </div>

        <div className="my-6 flex items-baseline gap-2">
          <span className={`text-6xl font-bold font-mono ${bandStyle.text}`}>
            {score.overall}
          </span>
          <span className="text-xl font-mono text-text-muted">/ 100</span>
        </div>

        <div>
          <div className="text-xs font-mono text-text-secondary flex items-center justify-between border-t border-border/60 pt-3">
            <span>Weighted Deterministic Index</span>
            <span className="text-text-primary">{totalFindings} Total Issues</span>
          </div>

          {onRescanClick && (
            <button
              onClick={onRescanClick}
              className="mt-3 w-full py-2 px-3 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-mono font-semibold transition-all flex items-center justify-center gap-1.5 shadow-sm"
            >
              <GitCompare className="w-3.5 h-3.5" />
              <span>Re-Scan Project</span>
            </button>
          )}
        </div>
      </div>

      {/* Severity Breakdown Box */}
      <div className="col-span-1 lg:col-span-2 p-6 rounded-xl border border-border bg-surface/60 flex flex-col justify-between">
        <div>
          <h3 className="text-xs font-mono text-text-secondary uppercase tracking-wider mb-4">
            Severity Distribution
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {/* Critical */}
            <div className="p-3 rounded-lg border border-red-500/20 bg-red-500/5">
              <div className="flex items-center gap-1.5 text-xs font-mono text-red-400 mb-1">
                <span className="w-2 h-2 rounded-full bg-red-500" />
                <span>Critical</span>
              </div>
              <div className="text-2xl font-bold font-mono text-red-400">
                {summary.critical}
              </div>
            </div>

            {/* High */}
            <div className="p-3 rounded-lg border border-orange-500/20 bg-orange-500/5">
              <div className="flex items-center gap-1.5 text-xs font-mono text-orange-400 mb-1">
                <span className="w-2 h-2 rounded-full bg-orange-500" />
                <span>High</span>
              </div>
              <div className="text-2xl font-bold font-mono text-orange-400">
                {summary.high}
              </div>
            </div>

            {/* Medium */}
            <div className="p-3 rounded-lg border border-amber-500/20 bg-amber-500/5">
              <div className="flex items-center gap-1.5 text-xs font-mono text-amber-400 mb-1">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                <span>Medium</span>
              </div>
              <div className="text-2xl font-bold font-mono text-amber-400">
                {summary.medium}
              </div>
            </div>

            {/* Low */}
            <div className="p-3 rounded-lg border border-blue-500/20 bg-blue-500/5">
              <div className="flex items-center gap-1.5 text-xs font-mono text-blue-400 mb-1">
                <span className="w-2 h-2 rounded-full bg-blue-500" />
                <span>Low</span>
              </div>
              <div className="text-2xl font-bold font-mono text-blue-400">
                {summary.low}
              </div>
            </div>

            {/* Info */}
            <div className="p-3 rounded-lg border border-zinc-500/20 bg-zinc-500/5">
              <div className="flex items-center gap-1.5 text-xs font-mono text-zinc-400 mb-1">
                <span className="w-2 h-2 rounded-full bg-zinc-400" />
                <span>Info</span>
              </div>
              <div className="text-2xl font-bold font-mono text-zinc-400">
                {summary.info}
              </div>
            </div>
          </div>
        </div>

        {/* Severity Progress Bar */}
        <div className="mt-4 pt-3 border-t border-border">
          <div className="w-full h-2 rounded-full bg-surface-elevated overflow-hidden flex">
            {summary.critical > 0 && (
              <div
                style={{ width: `${(summary.critical / totalFindings) * 100}%` }}
                className="bg-red-500 h-full"
              />
            )}
            {summary.high > 0 && (
              <div
                style={{ width: `${(summary.high / totalFindings) * 100}%` }}
                className="bg-orange-500 h-full"
              />
            )}
            {summary.medium > 0 && (
              <div
                style={{ width: `${(summary.medium / totalFindings) * 100}%` }}
                className="bg-amber-500 h-full"
              />
            )}
            {summary.low > 0 && (
              <div
                style={{ width: `${(summary.low / totalFindings) * 100}%` }}
                className="bg-blue-500 h-full"
              />
            )}
            {summary.info > 0 && (
              <div
                style={{ width: `${(summary.info / totalFindings) * 100}%` }}
                className="bg-zinc-500 h-full"
              />
            )}
            {totalFindings === 0 && (
              <div className="bg-emerald-500 h-full w-full" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
