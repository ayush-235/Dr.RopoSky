"use client";

import React from "react";
import { Shield, Terminal, ArrowUpRight, Github } from "lucide-react";

import { DrRopoSkyLogo } from "../brand/DrRopoSkyLogo";

interface NavbarProps {
  onReset?: () => void;
  onSampleClick?: (url: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onReset, onSampleClick }) => {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Brand */}
        <div
          onClick={onReset}
          className="cursor-pointer select-none group"
        >
          <DrRopoSkyLogo variant="compact" size="md" />
        </div>

        {/* Navigation & Sample */}
        <div className="flex items-center gap-3">
          {onSampleClick && (
            <button
              onClick={() => onSampleClick("https://github.com/expressjs/express")}
              className="text-xs font-mono px-3 py-1.5 rounded border border-border bg-surface/50 text-text-secondary hover:text-text-primary hover:border-border-active hover:bg-surface transition-all flex items-center gap-1.5"
            >
              <Github className="w-3.5 h-3.5" />
              <span>Demo Repo</span>
              <ArrowUpRight className="w-3 h-3 opacity-60" />
            </button>
          )}

          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded bg-surface/40 border border-border text-[11px] font-mono text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>SANDBOX SECURED</span>
          </div>
        </div>
      </div>
    </header>
  );
};
