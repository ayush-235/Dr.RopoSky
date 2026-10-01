"use client";

import React from "react";
import { SceneState } from "@/types/report";

interface CoreFallbackProps {
  state?: SceneState;
}

export const CoreFallback: React.FC<CoreFallbackProps> = ({ state = "idle" }) => {
  const isScanning = state === "scanning";
  const hasIssues = state === "issues";

  return (
    <div
      data-testid="3d-core-fallback"
      className="relative w-full h-full flex items-center justify-center select-none"
    >
      <svg
        viewBox="0 0 400 400"
        className="w-72 h-72 sm:w-96 sm:h-96"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle
          cx="200"
          cy="200"
          r="160"
          stroke="#26282e"
          strokeWidth="1"
          strokeDasharray="4 6"
          className="opacity-40 animate-[spin_60s_linear_infinite]"
        />
        <circle
          cx="200"
          cy="200"
          r="110"
          stroke="#00d2ff"
          strokeWidth="1"
          className={`opacity-30 ${isScanning ? "animate-[spin_10s_linear_infinite]" : ""}`}
        />
        <circle
          cx="200"
          cy="200"
          r="60"
          stroke="#a855f7"
          strokeWidth="1.5"
          className="opacity-50"
        />

        {/* Outer Orbit Nodes */}
        <circle cx="200" cy="40" r="6" fill="#00d2ff" className="opacity-80" />
        <circle cx="340" cy="200" r="5" fill="#a855f7" className="opacity-80" />
        <circle cx="200" cy="360" r="6" fill="#10b981" className="opacity-80" />
        <circle cx="60" cy="200" r="5" fill={hasIssues ? "#ef4444" : "#00d2ff"} className="opacity-80" />

        {/* Connection Lines */}
        <line x1="200" y1="40" x2="200" y2="200" stroke="#26282e" strokeWidth="1" />
        <line x1="340" y1="200" x2="200" y2="200" stroke="#26282e" strokeWidth="1" />
        <line x1="200" y1="360" x2="200" y2="200" stroke="#26282e" strokeWidth="1" />
        <line x1="60" y1="200" x2="200" y2="200" stroke="#26282e" strokeWidth="1" />

        {/* Central Core */}
        <circle
          cx="200"
          cy="200"
          r="24"
          fill="#121316"
          stroke={hasIssues ? "#ef4444" : "#00d2ff"}
          strokeWidth="2"
        />
        <circle
          cx="200"
          cy="200"
          r="10"
          fill={hasIssues ? "#ef4444" : isScanning ? "#00d2ff" : "#a855f7"}
          className={isScanning ? "animate-pulse" : ""}
        />
      </svg>
      <div className="absolute bottom-2 text-center text-xs font-mono text-text-muted">
        PROJECT ANALYSIS CORE
      </div>
    </div>
  );
};
