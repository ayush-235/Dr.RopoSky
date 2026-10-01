"use client";

import React from "react";
import { ProjectScanSummary } from "@/lib/api/client";
import { History, Shield, Calendar, Layers, AlertTriangle } from "lucide-react";

interface ScanHistoryCardProps {
  scans: ProjectScanSummary[];
  currentScanId?: string;
}

export const ScanHistoryCard: React.FC<ScanHistoryCardProps> = ({
  scans,
  currentScanId,
}) => {
  if (!scans || scans.length === 0) {
    return null;
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
    if (score >= 75) return "text-cyan-400 bg-cyan-500/10 border-cyan-500/30";
    if (score >= 60) return "text-amber-400 bg-amber-500/10 border-amber-500/30";
    return "text-rose-400 bg-rose-500/10 border-rose-500/30";
  };

  return (
    <div className="rounded-2xl border border-border bg-surface p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-primary" />
          <h2 className="text-sm font-bold font-mono text-text-primary uppercase tracking-wider">
            Audit Scan History ({scans.length})
          </h2>
        </div>
        <span className="text-[11px] font-mono text-text-muted">
          Persisted Audit Trail
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-xs">
          <thead>
            <tr className="border-b border-border text-text-muted text-[11px] pb-2">
              <th className="py-2.5 px-3 font-semibold">Scan Date & Time</th>
              <th className="py-2.5 px-3 font-semibold">Overall Score</th>
              <th className="py-2.5 px-3 font-semibold hidden md:table-cell">Security</th>
              <th className="py-2.5 px-3 font-semibold hidden md:table-cell">Reliability</th>
              <th className="py-2.5 px-3 font-semibold hidden lg:table-cell">Quality</th>
              <th className="py-2.5 px-3 font-semibold">Findings</th>
              <th className="py-2.5 px-3 font-semibold text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {scans.map((s, idx) => {
              const isCurrent = s.id === currentScanId || idx === 0;
              const dateStr = s.created_at
                ? new Date(s.created_at).toLocaleString(undefined, {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : "Unknown";

              return (
                <tr
                  key={s.id}
                  className={`hover:bg-surface-elevated/50 transition-colors ${
                    isCurrent ? "bg-primary/5" : ""
                  }`}
                >
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-3.5 h-3.5 text-text-muted" />
                      <span className="text-text-primary font-medium">{dateStr}</span>
                      {isCurrent && (
                        <span className="px-1.5 py-0.5 rounded bg-primary/20 text-primary text-[10px] font-bold">
                          Current
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-lg border font-bold text-xs ${getScoreColor(
                        s.overall_score
                      )}`}
                    >
                      {s.overall_score}/100
                    </span>
                  </td>
                  <td className="py-3 px-3 hidden md:table-cell text-text-secondary">
                    {s.security_score}/100
                  </td>
                  <td className="py-3 px-3 hidden md:table-cell text-text-secondary">
                    {s.reliability_score}/100
                  </td>
                  <td className="py-3 px-3 hidden lg:table-cell text-text-secondary">
                    {s.quality_score}/100
                  </td>
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-1.5">
                      <span className="text-text-primary font-semibold">
                        {s.total_findings}
                      </span>
                      {s.critical_count > 0 && (
                        <span className="px-1 py-0.2 rounded bg-rose-500/20 text-rose-400 text-[10px] font-bold">
                          {s.critical_count} crit
                        </span>
                      )}
                      {s.high_count > 0 && (
                        <span className="px-1 py-0.2 rounded bg-amber-500/20 text-amber-400 text-[10px] font-bold">
                          {s.high_count} high
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] uppercase font-bold">
                      {s.status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
