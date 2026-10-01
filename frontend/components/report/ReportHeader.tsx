"use client";

import React from "react";
import { ProjectMetadata, AnalysisExecutionInfo, AnalysisReport } from "@/types/report";
import { formatDuration, formatDate } from "@/lib/utils";
import { GitBranch, Clock, FileCode, Download, RefreshCw, GitCompare, Layers } from "lucide-react";

interface ReportHeaderProps {
  project: ProjectMetadata;
  analysis: AnalysisExecutionInfo;
  report: AnalysisReport;
  onNewScan: () => void;
  onRescanClick?: () => void;
}

export const ReportHeader: React.FC<ReportHeaderProps> = ({
  project,
  analysis,
  report,
  onNewScan,
  onRescanClick,
}) => {
  const downloadJson = () => {
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(report, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `dr-roposky-audit-${project.name}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="w-full border-b border-border bg-surface/60 backdrop-blur-md p-6 rounded-xl border mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Project Title & Metadata */}
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-text-muted mb-1">
            <span className="uppercase px-2 py-0.5 rounded bg-surface-elevated border border-border text-primary">
              {project.source_type}
            </span>
            <span>&bull;</span>
            <span>Scanned {formatDate(analysis.started_at)}</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold font-mono text-text-primary tracking-tight">
            {project.name}
          </h1>

          {/* Languages & Manifests */}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {(project.languages || []).map((lang) => (
              <span
                key={lang}
                className="text-xs font-mono px-2 py-0.5 rounded bg-surface border border-border text-text-secondary"
              >
                {lang}
              </span>
            ))}
            {(project.manifests || []).map((manifest) => (
              <span
                key={manifest}
                className="text-xs font-mono px-2 py-0.5 rounded bg-surface border border-border-subtle text-text-muted"
              >
                {manifest}
              </span>
            ))}
          </div>
        </div>

        {/* Quick Stats & Actions */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-4 px-3 py-2 rounded-lg bg-surface border border-border text-xs font-mono text-text-secondary">
            <div className="flex items-center gap-1.5">
              <FileCode className="w-3.5 h-3.5 text-primary" />
              <span>{analysis.files_analyzed} Files</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-text-muted" />
              <span>{formatDuration(analysis.duration_ms)}</span>
            </div>
          </div>

          <button
            onClick={downloadJson}
            className="px-3 py-2 rounded-lg bg-surface hover:bg-surface-elevated border border-border hover:border-border-active text-xs font-mono text-text-primary transition-all flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </button>

          {onRescanClick && (
            <button
              onClick={onRescanClick}
              className="px-3 py-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono font-semibold text-xs transition-all flex items-center gap-1.5 shadow-sm"
            >
              <GitCompare className="w-3.5 h-3.5" />
              <span>Re-Scan & Compare</span>
            </button>
          )}

          <button
            onClick={onNewScan}
            className="px-3 py-2 rounded-lg bg-primary hover:bg-primary-hover text-background font-mono font-semibold text-xs transition-all flex items-center gap-1.5 shadow-sm shadow-primary/20"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>New Scan</span>
          </button>
        </div>
      </div>
    </div>
  );
};
