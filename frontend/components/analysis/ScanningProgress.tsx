"use client";

import React, { useState, useEffect } from "react";
import { SCANNING_STEPS } from "@/lib/constants";
import { Download, Search, Cpu, Shield, Sparkles, Calculator, CheckCircle2 } from "lucide-react";

interface ScanningProgressProps {
  targetName: string;
}

export const ScanningProgress: React.FC<ScanningProgressProps> = ({ targetName }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [elapsedSec, setElapsedSec] = useState(0);

  const iconMap: Record<string, any> = {
    Download,
    Search,
    Cpu,
    Shield,
    Sparkles,
    Calculator,
  };

  useEffect(() => {
    // Timer for elapsed seconds
    const timer = setInterval(() => {
      setElapsedSec((prev) => prev + 1);
    }, 1000);

    // Progress through conceptual pipeline stages while awaiting response
    const stepInterval = setInterval(() => {
      setCurrentStepIndex((prev) => {
        if (prev < SCANNING_STEPS.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 1800);

    return () => {
      clearInterval(timer);
      clearInterval(stepInterval);
    };
  }, []);

  return (
    <div className="w-full max-w-2xl mx-auto rounded-xl border border-border bg-surface/90 backdrop-blur-md p-6 shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-border mb-6">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-primary animate-ping" />
          <div>
            <h2 className="text-sm font-bold font-mono text-text-primary tracking-wide">
              AUDIT ANALYSIS IN PROGRESS
            </h2>
            <p className="text-xs font-mono text-text-secondary truncate max-w-md">
              Target: {targetName}
            </p>
          </div>
        </div>
        <div className="px-2.5 py-1 rounded bg-surface-elevated border border-border text-xs font-mono text-primary">
          {elapsedSec}s elapsed
        </div>
      </div>

      {/* Steps List */}
      <div className="space-y-3.5">
        {SCANNING_STEPS.map((step, index) => {
          const isDone = index < currentStepIndex;
          const isCurrent = index === currentStepIndex;
          const isPending = index > currentStepIndex;
          const Icon = iconMap[step.icon] || Cpu;

          return (
            <div
              key={step.id}
              className={`flex items-center justify-between p-3 rounded-lg border transition-all ${
                isCurrent
                  ? "bg-primary/5 border-primary/40 text-text-primary shadow-sm"
                  : isDone
                  ? "bg-surface-elevated/40 border-border text-text-secondary"
                  : "bg-transparent border-border/40 text-text-muted opacity-60"
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-7 h-7 rounded flex items-center justify-center text-xs font-mono transition-colors ${
                    isDone
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : isCurrent
                      ? "bg-primary/20 text-primary border border-primary/40"
                      : "bg-surface border border-border text-text-muted"
                  }`}
                >
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Icon className="w-3.5 h-3.5" />
                  )}
                </div>
                <span className="text-xs font-mono font-medium">
                  {step.label}
                </span>
              </div>

              <div className="text-[11px] font-mono">
                {isDone && <span className="text-emerald-400">DONE</span>}
                {isCurrent && (
                  <span className="text-primary flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                    RUNNING
                  </span>
                )}
                {isPending && <span className="text-text-muted">QUEUED</span>}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="mt-6 pt-4 border-t border-border flex items-center justify-between text-[11px] font-mono text-text-muted">
        <span>🛡️ Sandboxed Subprocess Security</span>
        <span>Deterministic Rule Evaluation</span>
      </div>
    </div>
  );
};
