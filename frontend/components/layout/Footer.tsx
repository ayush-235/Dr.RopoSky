import React from "react";
import { ShieldCheck, Lock } from "lucide-react";
import { DrRopoSkyLogo } from "../brand/DrRopoSkyLogo";

export const Footer: React.FC = () => {
  return (
    <footer className="w-full border-t border-border bg-surface/30 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-text-muted">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-text-secondary">
            <Lock className="w-3.5 h-3.5 text-primary" />
            <span>Zero Untrusted Code Execution</span>
          </div>
          <span className="text-border">|</span>
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Deterministic Scoring</span>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3 text-center sm:text-right">
          <DrRopoSkyLogo variant="compact" size="sm" />
          <span className="hidden sm:inline text-border">&bull;</span>
          <span className="text-[11px] text-text-secondary">AI-powered full-project software auditor</span>
        </div>
      </div>
    </footer>
  );
};
