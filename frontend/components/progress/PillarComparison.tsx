"use client";

import React from "react";
import { PillarsDelta } from "@/types/report";
import { formatDelta, getDeltaStyle } from "@/lib/utils";
import {
  ShieldAlert,
  Bug,
  Sparkles,
  Zap,
  Layers,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";

interface PillarComparisonProps {
  pillarsDelta: PillarsDelta;
}

interface PillarConfig {
  key: keyof PillarsDelta;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const PILLARS: PillarConfig[] = [
  {
    key: "security",
    label: "Security & Vulnerabilities",
    icon: ShieldAlert,
    description: "Secrets, SAST, CVE dependencies, injection",
  },
  {
    key: "reliability",
    label: "Reliability & Bugs",
    icon: Bug,
    description: "AST syntax, runtime errors, type traps",
  },
  {
    key: "code_quality",
    label: "Code Quality",
    icon: Sparkles,
    description: "Linting, style guidelines, maintainability",
  },
  {
    key: "performance",
    label: "Performance",
    icon: Zap,
    description: "Time complexity, blocking calls, resource leaks",
  },
  {
    key: "architecture",
    label: "Architecture & Design",
    icon: Layers,
    description: "Modularity, circular imports, layered boundaries",
  },
  {
    key: "completeness",
    label: "Completeness",
    icon: CheckCircle2,
    description: "README, license, gitignore, test coverage",
  },
];

export const PillarComparison: React.FC<PillarComparisonProps> = ({ pillarsDelta }) => {
  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-bold font-mono text-text-primary uppercase tracking-wider">
            Pillar-by-Pillar Progress
          </h2>
          <p className="text-xs font-mono text-text-muted mt-0.5">
            Deterministic delta across all 6 core analysis dimensions
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {PILLARS.map((p) => {
          const item = pillarsDelta[p.key];
          if (!item) return null;

          const deltaStyle = getDeltaStyle(item.delta);
          const Icon = p.icon;

          return (
            <div
              key={p.key}
              className="p-5 rounded-xl border border-border bg-surface hover:border-border-active transition-all flex flex-col justify-between"
            >
              {/* Pillar Header */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-surface-elevated border border-border text-primary">
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-bold font-mono text-text-primary">
                      {p.label}
                    </span>
                  </div>

                  {/* Delta Pill */}
                  <div
                    className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono font-bold border ${deltaStyle.badge}`}
                  >
                    {item.delta > 0 && <TrendingUp className="w-3 h-3 text-emerald-400" />}
                    {item.delta < 0 && <TrendingDown className="w-3 h-3 text-rose-400" />}
                    {item.delta === 0 && <Minus className="w-3 h-3 text-text-muted" />}
                    <span>{formatDelta(item.delta)}</span>
                  </div>
                </div>

                <p className="text-[11px] font-mono text-text-muted mb-4 line-clamp-1">
                  {p.description}
                </p>
              </div>

              {/* Pillar Scores & Bar */}
              <div>
                <div className="flex items-baseline justify-between mb-1.5 font-mono text-xs">
                  <div className="text-text-muted">
                    <span>Prev: </span>
                    <span className="text-text-secondary line-through opacity-75">{item.previous}</span>
                  </div>
                  <div className="text-text-primary font-bold">
                    <span>Curr: </span>
                    <span className="text-sm text-primary">{item.current}</span>
                    <span className="text-[10px] text-text-muted">/100</span>
                  </div>
                </div>

                {/* Progress Visual Bar */}
                <div className="w-full h-1.5 rounded-full bg-surface-elevated overflow-hidden relative">
                  {/* Previous indicator mark */}
                  <div
                    className="absolute top-0 bottom-0 bg-text-muted/40 z-0"
                    style={{ width: `${Math.min(100, Math.max(0, item.previous))}%` }}
                  />
                  {/* Current progress bar */}
                  <div
                    className={`h-full rounded-full transition-all duration-500 z-10 relative ${
                      item.delta >= 0 ? "bg-primary" : "bg-rose-400"
                    }`}
                    style={{ width: `${Math.min(100, Math.max(0, item.current))}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
