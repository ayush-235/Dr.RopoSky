"use client";

import React from "react";
import { ScannerExecutionResult } from "@/types/report";
import { formatDuration, formatScannerName } from "@/lib/utils";
import { CheckCircle2, XCircle, AlertCircle, MinusCircle } from "lucide-react";

interface ScannerListProps {
  scanners: ScannerExecutionResult[];
}

export const ScannerList: React.FC<ScannerListProps> = ({ scanners }) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "success":
        return (
          <span className="flex items-center gap-1 text-emerald-400 text-xs font-mono">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Executed</span>
          </span>
        );
      case "unavailable":
        return (
          <span className="flex items-center gap-1 text-text-muted text-xs font-mono">
            <MinusCircle className="w-3.5 h-3.5" />
            <span>Unavailable</span>
          </span>
        );
      case "skipped":
        return (
          <span className="flex items-center gap-1 text-text-muted text-xs font-mono">
            <MinusCircle className="w-3.5 h-3.5" />
            <span>Skipped</span>
          </span>
        );
      case "failed":
      default:
        return (
          <span className="flex items-center gap-1 text-red-400 text-xs font-mono">
            <XCircle className="w-3.5 h-3.5" />
            <span>Failed</span>
          </span>
        );
    }
  };

  return (
    <div className="p-5 rounded-xl border border-border bg-surface/40 mb-8">
      <h3 className="text-xs font-mono text-text-secondary uppercase tracking-wider mb-3">
        Static & Cybersecurity Scanner Suite
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {scanners.map((scan) => (
          <div
            key={scan.scanner}
            className="p-3 rounded-lg border border-border bg-surface flex items-center justify-between"
          >
            <div>
              <div className="text-xs font-mono font-semibold text-text-primary">
                {formatScannerName(scan.scanner)}
              </div>
              <div className="text-[11px] font-mono text-text-muted">
                {scan.findings_count} finding{scan.findings_count !== 1 ? "s" : ""} &bull; {formatDuration(scan.duration_ms)}
              </div>
            </div>
            <div>{getStatusBadge(scan.status)}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
