"use client";

import React, { useEffect } from "react";
import { AlertCircle, RotateCcw, Home } from "lucide-react";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorBoundary({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log sanitized client error
    console.error("Dr.RopoSky UI error caught by boundary:", error.message);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-background text-text-primary">
      <div className="max-w-lg w-full p-6 sm:p-8 rounded-2xl border border-red-500/30 bg-surface shadow-2xl flex flex-col items-center text-center">
        <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 flex items-center justify-center mb-4">
          <AlertCircle className="w-6 h-6" />
        </div>

        <h1 className="text-lg font-bold font-mono text-text-primary mb-2">
          Application Interface Error
        </h1>

        <p className="text-xs font-mono text-text-secondary leading-relaxed mb-6 max-w-sm">
          An unexpected interface exception occurred while rendering the project report. The system remains operational.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3 w-full">
          <button
            onClick={() => reset()}
            className="flex-1 sm:flex-initial px-4 py-2.5 rounded-lg bg-primary hover:bg-primary-hover text-background font-mono font-semibold text-xs transition-all flex items-center justify-center gap-2 shadow-sm"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
          <button
            onClick={() => {
              window.location.href = "/";
            }}
            className="flex-1 sm:flex-initial px-4 py-2.5 rounded-lg bg-surface-elevated hover:bg-surface border border-border text-xs font-mono text-text-primary transition-all flex items-center justify-center gap-2"
          >
            <Home className="w-3.5 h-3.5" />
            <span>Return to Home</span>
          </button>
        </div>
      </div>
    </div>
  );
}
