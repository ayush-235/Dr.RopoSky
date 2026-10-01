"use client";

import React from "react";
import { ProjectScore } from "@/types/report";
import { SCORING_PILLARS } from "@/lib/constants";
import { Shield, Bug, CheckCircle2, Cpu, Layers, Sparkles } from "lucide-react";

interface PillarGridProps {
  score: ProjectScore;
}

export const PillarGrid: React.FC<PillarGridProps> = ({ score }) => {
  const iconMap: Record<string, any> = {
    security: Shield,
    reliability: Bug,
    code_quality: CheckCircle2,
    performance: Cpu,
    architecture: Layers,
    completeness: Sparkles,
  };

  const getScoreColor = (val: number) => {
    if (val >= 80) return "text-emerald-400 border-emerald-500/30 bg-emerald-500/10";
    if (val >= 60) return "text-cyan-400 border-cyan-500/30 bg-cyan-500/10";
    if (val >= 40) return "text-amber-400 border-amber-500/30 bg-amber-500/10";
    return "text-red-400 border-red-500/30 bg-red-500/10";
  };

  return (
    <div className="mb-8">
      <h2 className="text-xs font-mono text-text-secondary uppercase tracking-wider mb-4">
        Engineering & Security Pillar Breakdown
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {SCORING_PILLARS.map((pillar) => {
          const catScore = score.categories?.[pillar.key];
          const pillarVal =
            catScore?.score ??
            (score as any)[pillar.key] ??
            100;
          const findingCount = catScore?.finding_count ?? 0;
          const deductions = catScore?.deductions ?? 0;
          const explanation = catScore?.explanation || "";

          const Icon = iconMap[pillar.key] || Shield;
          const style = getScoreColor(pillarVal);

          return (
            <div
              key={pillar.key}
              className="p-5 rounded-xl border border-border bg-surface/60 hover:bg-surface transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2 text-text-primary">
                    <div className="w-7 h-7 rounded bg-surface-elevated border border-border flex items-center justify-center text-primary">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="font-mono text-sm font-semibold">
                      {pillar.name}
                    </span>
                  </div>

                  <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded-full border ${style}`}>
                    {pillarVal} / 100
                  </span>
                </div>

                <div className="w-full h-1.5 rounded-full bg-surface-elevated overflow-hidden mb-3">
                  <div
                    style={{ width: `${pillarVal}%` }}
                    className={`h-full ${
                      pillarVal >= 80
                        ? "bg-emerald-500"
                        : pillarVal >= 60
                        ? "bg-cyan-500"
                        : pillarVal >= 40
                        ? "bg-amber-500"
                        : "bg-red-500"
                    }`}
                  />
                </div>

                <p className="text-xs font-mono text-text-secondary leading-relaxed">
                  {explanation || pillar.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-border/60 flex items-center justify-between text-[11px] font-mono text-text-muted">
                <span>Weight: {pillar.weight}</span>
                <span>
                  {findingCount > 0 ? (
                    <span className="text-amber-400">
                      {findingCount} finding{findingCount !== 1 ? "s" : ""} (-{deductions} pts)
                    </span>
                  ) : (
                    <span className="text-emerald-400">Clean baseline</span>
                  )}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
