"use client";

import { ComparisonReport } from "@/types/report";
import { ProjectScanSummary } from "@/lib/api/client";
import { ScoreComparison } from "./ScoreComparison";
import { PillarComparison } from "./PillarComparison";
import { FindingChanges } from "./FindingChanges";
import { ScanHistoryCard } from "./ScanHistoryCard";
import {
  RefreshCw,
  GitCompare,
} from "lucide-react";

interface ProgressDashboardProps {
  comparison: ComparisonReport;
  onTriggerRescan?: () => void;
  scanHistory?: ProjectScanSummary[];
  currentScanId?: string;
}

export const ProgressDashboard: React.FC<ProgressDashboardProps> = ({
  comparison,
  onTriggerRescan,
  scanHistory,
  currentScanId,
}) => {
  const {
    summary,
    overall,
    pillars,
    fixed_findings,
    new_findings,
    remaining_findings,
    changed_findings,
  } = comparison;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* 1. Comparison Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl border border-border bg-surface/80 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-primary mb-1">
            <GitCompare className="w-4 h-4" />
            <span className="font-bold tracking-wider uppercase">
              Delta Analysis Mode &bull; Scan Progress
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold font-mono text-text-primary">
            Verification & Progress Tracking
          </h1>
          <p className="text-xs font-mono text-text-muted mt-1">
            Deterministic diff comparing baseline scan against the current re-scan.
          </p>
        </div>

        {onTriggerRescan && (
          <button
            onClick={onTriggerRescan}
            className="px-4 py-2.5 rounded-xl bg-surface-elevated hover:bg-surface border border-border hover:border-primary/50 text-xs font-mono text-text-primary transition-all flex items-center gap-2 shrink-0 self-start sm:self-auto"
          >
            <RefreshCw className="w-3.5 h-3.5 text-primary" />
            <span>Re-Scan Project Again</span>
          </button>
        )}
      </div>

      {/* 2. Score Transition Component */}
      <ScoreComparison scoreDelta={overall} />

      {/* 3. Pillar-by-Pillar Delta Breakdown */}
      <PillarComparison pillarsDelta={pillars} />

      {/* 4. Categorized Finding Delta Explorer */}
      <div className="pt-2">
        <div className="mb-4">
          <h2 className="text-sm font-bold font-mono text-text-primary uppercase tracking-wider">
            Detailed Issue Delta Explorer
          </h2>
          <p className="text-xs font-mono text-text-muted mt-0.5">
            Compare resolved vulnerabilities, regressions, and remaining issues
          </p>
        </div>

        <FindingChanges
          summary={summary}
          fixedFindings={fixed_findings}
          newFindings={new_findings}
          remainingFindings={remaining_findings}
          changedFindings={changed_findings}
        />
      </div>

      {/* 5. Scan History Trail */}
      {scanHistory && scanHistory.length > 0 && (
        <ScanHistoryCard scans={scanHistory} currentScanId={currentScanId} />
      )}
    </div>
  );
};
