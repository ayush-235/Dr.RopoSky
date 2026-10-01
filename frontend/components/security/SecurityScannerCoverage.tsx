"use client";

import React from "react";
import { ScannerExecutionResult } from "@/types/report";
import { formatDuration, formatScannerName } from "@/lib/utils";
import { CheckCircle2, XCircle, MinusCircle, ShieldCheck } from "lucide-react";

interface SecurityScannerCoverageProps {
  scanners: ScannerExecutionResult[];
}

export const SecurityScannerCoverage: React.FC<SecurityScannerCoverageProps> = ({
  scanners,
}) => {
  // Filter for security-relevant scanners
  const securityScanners = scanners.filter((s) =>
    [
      "rokospy-secret-scanner",
      "gitleaks",
      "semgrep",
      "bandit",
      "npm-audit",
      "pip-audit",
    ].includes(s.scanner)
  );

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "success":
        return (
          <span className="flex items-center gap-1 text-emerald-400 text-xs font-mono font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Active</span>
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
          <span className="flex items-center gap-1 text-red-400 text-xs font-mono font-medium">
            <XCircle className="w-3.5 h-3.5" />
            <span>Error</span>
          </span>
        );
    }
  };

  return (
    <div className="p-5 rounded-xl border border-border bg-surface/60 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-primary" />
          <h3 className="text-xs font-mono font-bold text-text-primary uppercase tracking-wider">
            Cybersecurity Scanner Coverage & Telemetry
          </h3>
        </div>
        <span className="text-[11px] font-mono text-text-muted">
          Sandboxed execution without code execution
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {securityScanners.map((scan) => (
          <div
            key={scan.scanner}
            className="p-3.5 rounded-lg border border-border bg-surface flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono font-bold text-text-primary">
                {formatScannerName(scan.scanner)}
              </span>
              {getStatusBadge(scan.status)}
            </div>

            <div className="flex items-center justify-between text-[11px] font-mono text-text-muted border-t border-border-subtle pt-2 mt-1">
              <span>{scan.findings_count} finding{scan.findings_count !== 1 ? "s" : ""}</span>
              <span>{formatDuration(scan.duration_ms)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
