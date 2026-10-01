"use client";

import React from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import { ProjectScore } from "@/types/report";
import { SCORING_PILLARS } from "@/lib/constants";

interface PillarChartProps {
  score: ProjectScore;
}

export const PillarChart: React.FC<PillarChartProps> = ({ score }) => {
  const chartData = SCORING_PILLARS.map((p) => {
    const val =
      score.categories?.[p.key]?.score ??
      (score as any)[p.key] ??
      100;
    return {
      subject: p.name,
      score: val,
      fullMark: 100,
    };
  });

  return (
    <div className="w-full h-64 sm:h-72 p-4 rounded-xl border border-border bg-surface/40 flex flex-col items-center justify-center">
      <span className="text-xs font-mono text-text-secondary uppercase tracking-wider mb-2 self-start">
        6-Pillar Radar Posture
      </span>
      <div className="w-full h-full min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
            <PolarGrid stroke="#26282e" />
            <PolarAngleAxis
              dataKey="subject"
              tick={{ fill: "#8c8f9a", fontSize: 11, fontFamily: "monospace" }}
            />
            <PolarRadiusAxis
              angle={30}
              domain={[0, 100]}
              tick={{ fill: "#5a5d68", fontSize: 10 }}
              stroke="#26282e"
            />
            <Radar
              name="Engineering Score"
              dataKey="score"
              stroke="#00d2ff"
              fill="#00d2ff"
              fillOpacity={0.25}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
