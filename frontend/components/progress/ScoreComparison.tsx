"use client";

import React from "react";
import { ScoreDelta } from "@/types/report";
import { formatDelta, getDeltaStyle, getRatingBandColor, getRatingBandFromScore } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus, ArrowRight } from "lucide-react";

interface ScoreComparisonProps {
  scoreDelta: ScoreDelta;
}

export const ScoreComparison: React.FC<ScoreComparisonProps> = ({ scoreDelta }) => {
  const deltaStyle = getDeltaStyle(scoreDelta.delta);
  const prevBand = getRatingBandFromScore(scoreDelta.previous);
  const currBand = getRatingBandFromScore(scoreDelta.current);
  const prevBandStyle = getRatingBandColor(prevBand);
  const currBandStyle = getRatingBandColor(currBand);

  return (
    <div className="relative overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-surface via-surface to-surface-elevated/40 p-6 sm:p-8 backdrop-blur-sm">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        {/* Left Section: Score Transition Visualizer */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
          {/* Previous Score */}
          <div className="flex flex-col">
            <span className="text-xs font-mono text-text-muted uppercase tracking-wider mb-1">
              Previous Score
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl sm:text-4xl font-black font-mono text-text-muted line-through opacity-70">
                {scoreDelta.previous}
              </span>
              <span className="text-xs font-mono text-text-muted">/100</span>
            </div>
            <span className={`text-[11px] font-mono mt-1 px-2 py-0.5 rounded w-fit border ${prevBandStyle.badge} opacity-70`}>
              {prevBand}
            </span>
          </div>

          {/* Transition Arrow */}
          <div className="flex items-center justify-center p-2 rounded-full bg-surface-elevated border border-border text-text-muted self-center">
            <ArrowRight className="w-5 h-5" />
          </div>

          {/* Current Score */}
          <div className="flex flex-col">
            <span className="text-xs font-mono text-text-muted uppercase tracking-wider mb-1">
              Current Score
            </span>
            <div className="flex items-baseline gap-2">
              <span className={`text-4xl sm:text-5xl font-black font-mono tracking-tight ${currBandStyle.text}`}>
                {scoreDelta.current}
              </span>
              <span className="text-sm font-mono text-text-muted">/100</span>
            </div>
            <span className={`text-xs font-mono font-semibold mt-1 px-2.5 py-0.5 rounded-full w-fit border ${currBandStyle.badge}`}>
              {currBand}
            </span>
          </div>
        </div>

        {/* Right Section: Delta Pill & Progress Evaluation */}
        <div className="flex flex-col items-start lg:items-end justify-center border-t lg:border-t-0 lg:border-l border-border pt-4 lg:pt-0 lg:pl-8">
          <div className="text-xs font-mono text-text-muted mb-1.5">
            Net Score Progression
          </div>

          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border font-mono font-bold text-lg sm:text-xl ${deltaStyle.badge}`}>
            {scoreDelta.delta > 0 && <TrendingUp className="w-5 h-5 text-emerald-400" />}
            {scoreDelta.delta < 0 && <TrendingDown className="w-5 h-5 text-rose-400" />}
            {scoreDelta.delta === 0 && <Minus className="w-5 h-5 text-text-muted" />}
            <span>{formatDelta(scoreDelta.delta)} pts</span>
          </div>

          <p className="text-xs font-mono text-text-secondary mt-2 max-w-xs lg:text-right">
            {scoreDelta.delta > 0 && "Great improvement! Vulnerabilities and quality issues have been resolved."}
            {scoreDelta.delta < 0 && "Score regression detected. New findings or regressions were introduced."}
            {scoreDelta.delta === 0 && "Score unchanged between scans."}
          </p>
        </div>
      </div>
    </div>
  );
};
