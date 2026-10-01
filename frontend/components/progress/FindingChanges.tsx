"use client";

import React, { useState, useMemo } from "react";
import {
  ComparisonSummary,
  FindingChangeStatus,
  NormalizedFinding,
  FindingComparisonItem,
} from "@/types/report";
import { getSeverityStyle, getCategoryLabel } from "@/lib/utils";
import { FindingDetail } from "@/components/findings/FindingDetail";
import {
  CheckCircle2,
  AlertTriangle,
  Clock,
  RefreshCw,
  Search,
  ArrowRight,
  FileCode,
} from "lucide-react";

interface FindingChangesProps {
  summary: ComparisonSummary;
  fixedFindings: NormalizedFinding[];
  newFindings: NormalizedFinding[];
  remainingFindings: NormalizedFinding[];
  changedFindings: FindingComparisonItem[];
}

interface UnifiedFindingItem {
  status: FindingChangeStatus;
  finding: NormalizedFinding;
  previousFinding?: NormalizedFinding | null;
  changeDetails?: string | null;
}

export const FindingChanges: React.FC<FindingChangesProps> = ({
  summary,
  fixedFindings,
  newFindings,
  remainingFindings,
  changedFindings,
}) => {
  const [activeTab, setActiveTab] = useState<"ALL" | FindingChangeStatus>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedItemIndex, setSelectedItemIndex] = useState<number>(0);

  const allItems: UnifiedFindingItem[] = useMemo(() => {
    const list: UnifiedFindingItem[] = [];

    fixedFindings.forEach((f) => {
      list.push({
        status: "fixed",
        finding: f,
        previousFinding: f,
      });
    });

    newFindings.forEach((f) => {
      list.push({
        status: "new",
        finding: f,
        previousFinding: null,
      });
    });

    remainingFindings.forEach((f) => {
      list.push({
        status: "remaining",
        finding: f,
        previousFinding: f,
      });
    });

    changedFindings.forEach((c) => {
      list.push({
        status: "changed",
        finding: c.finding,
        previousFinding: c.previous_finding,
        changeDetails: c.change_details,
      });
    });

    return list;
  }, [fixedFindings, newFindings, remainingFindings, changedFindings]);

  const filteredFindings = useMemo(() => {
    return allItems.filter((item) => {
      // Tab filter
      if (activeTab !== "ALL" && item.status !== activeTab) {
        return false;
      }

      // Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const f = item.finding;
        const matchTitle = f.title?.toLowerCase().includes(q);
        const matchMessage = f.message?.toLowerCase().includes(q);
        const matchFile = (f.file_path || (f as any).file || "").toLowerCase().includes(q);
        const matchRule = f.rule_id?.toLowerCase().includes(q);
        const matchScanner = f.scanner?.toLowerCase().includes(q);

        return matchTitle || matchMessage || matchFile || matchRule || matchScanner;
      }

      return true;
    });
  }, [allItems, activeTab, searchQuery]);

  const selectedItem: UnifiedFindingItem | undefined =
    filteredFindings[selectedItemIndex] || filteredFindings[0];

  const getStatusBadge = (status: FindingChangeStatus) => {
    switch (status) {
      case "fixed":
        return {
          label: "Fixed",
          badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
          icon: CheckCircle2,
        };
      case "new":
        return {
          label: "New",
          badge: "bg-rose-500/10 text-rose-400 border-rose-500/30",
          icon: AlertTriangle,
        };
      case "changed":
        return {
          label: "Changed",
          badge: "bg-purple-500/10 text-purple-400 border-purple-500/30",
          icon: RefreshCw,
        };
      case "remaining":
      default:
        return {
          label: "Remaining",
          badge: "bg-surface-elevated text-text-muted border-border",
          icon: Clock,
        };
    }
  };

  return (
    <div className="w-full space-y-6">
      {/* 1. Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Fixed Card */}
        <button
          onClick={() => {
            setActiveTab("fixed");
            setSelectedItemIndex(0);
          }}
          className={`p-4 rounded-xl border transition-all text-left flex flex-col justify-between ${
            activeTab === "fixed"
              ? "bg-emerald-500/10 border-emerald-500/50 shadow-md shadow-emerald-500/5"
              : "bg-surface border-border hover:border-border-active"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-semibold text-emerald-400">
              Resolved Issues
            </span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-black font-mono text-emerald-400">
            {summary.fixed_count}
          </div>
          <span className="text-[10px] font-mono text-text-muted mt-1">
            Eliminated in re-scan
          </span>
        </button>

        {/* New Card */}
        <button
          onClick={() => {
            setActiveTab("new");
            setSelectedItemIndex(0);
          }}
          className={`p-4 rounded-xl border transition-all text-left flex flex-col justify-between ${
            activeTab === "new"
              ? "bg-rose-500/10 border-rose-500/50 shadow-md shadow-rose-500/5"
              : "bg-surface border-border hover:border-border-active"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-semibold text-rose-400">
              New Findings
            </span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-black font-mono text-rose-400">
            {summary.new_count}
          </div>
          <span className="text-[10px] font-mono text-text-muted mt-1">
            Introduced regressions
          </span>
        </button>

        {/* Remaining Card */}
        <button
          onClick={() => {
            setActiveTab("remaining");
            setSelectedItemIndex(0);
          }}
          className={`p-4 rounded-xl border transition-all text-left flex flex-col justify-between ${
            activeTab === "remaining"
              ? "bg-surface-elevated border-text-muted shadow-md"
              : "bg-surface border-border hover:border-border-active"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-semibold text-text-secondary">
              Remaining
            </span>
            <Clock className="w-4 h-4 text-text-muted" />
          </div>
          <div className="text-2xl sm:text-3xl font-black font-mono text-text-primary">
            {summary.remaining_count}
          </div>
          <span className="text-[10px] font-mono text-text-muted mt-1">
            Persisting unresolved
          </span>
        </button>

        {/* Changed Card */}
        <button
          onClick={() => {
            setActiveTab("changed");
            setSelectedItemIndex(0);
          }}
          className={`p-4 rounded-xl border transition-all text-left flex flex-col justify-between ${
            activeTab === "changed"
              ? "bg-purple-500/10 border-purple-500/50 shadow-md shadow-purple-500/5"
              : "bg-surface border-border hover:border-border-active"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-semibold text-purple-400">
              Changed
            </span>
            <RefreshCw className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-black font-mono text-purple-400">
            {summary.changed_count}
          </div>
          <span className="text-[10px] font-mono text-text-muted mt-1">
            Modified properties
          </span>
        </button>
      </div>

      {/* 2. Controls: Filter Tabs + Search */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-surface border border-border rounded-xl overflow-x-auto">
          <button
            onClick={() => {
              setActiveTab("ALL");
              setSelectedItemIndex(0);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
              activeTab === "ALL"
                ? "bg-surface-elevated text-text-primary font-bold border border-border"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            All Changes ({allItems.length})
          </button>
          <button
            onClick={() => {
              setActiveTab("fixed");
              setSelectedItemIndex(0);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all flex items-center gap-1.5 ${
              activeTab === "fixed"
                ? "bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/30"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            <span>Fixed</span>
            <span className="px-1.5 py-0.2 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px]">
              {summary.fixed_count}
            </span>
          </button>
          <button
            onClick={() => {
              setActiveTab("new");
              setSelectedItemIndex(0);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all flex items-center gap-1.5 ${
              activeTab === "new"
                ? "bg-rose-500/10 text-rose-400 font-bold border border-rose-500/30"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            <span>New</span>
            <span className="px-1.5 py-0.2 rounded-full bg-rose-500/20 text-rose-400 text-[10px]">
              {summary.new_count}
            </span>
          </button>
          <button
            onClick={() => {
              setActiveTab("remaining");
              setSelectedItemIndex(0);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all flex items-center gap-1.5 ${
              activeTab === "remaining"
                ? "bg-surface-elevated text-text-primary font-bold border border-border"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            <span>Remaining</span>
            <span className="px-1.5 py-0.2 rounded-full bg-surface border border-border text-[10px]">
              {summary.remaining_count}
            </span>
          </button>
          {summary.changed_count > 0 && (
            <button
              onClick={() => {
                setActiveTab("changed");
                setSelectedItemIndex(0);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all flex items-center gap-1.5 ${
                activeTab === "changed"
                  ? "bg-purple-500/10 text-purple-400 font-bold border border-purple-500/30"
                  : "text-text-muted hover:text-text-secondary"
              }`}
            >
              <span>Changed</span>
              <span className="px-1.5 py-0.2 rounded-full bg-purple-500/20 text-purple-400 text-[10px]">
                {summary.changed_count}
              </span>
            </button>
          )}
        </div>

        {/* Search input */}
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
          <input
            type="text"
            placeholder="Search delta findings..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setSelectedItemIndex(0);
            }}
            className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-surface border border-border text-xs font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary/50"
          />
        </div>
      </div>

      {/* 3. Master / Detail Layout */}
      {filteredFindings.length === 0 ? (
        <div className="p-8 text-center rounded-xl border border-border bg-surface">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
          <h3 className="text-sm font-bold font-mono text-text-primary">
            No Findings in this Filter
          </h3>
          <p className="text-xs font-mono text-text-muted mt-1">
            No issues match the selected delta status or search criteria.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Findings List (Left column) */}
          <div className="lg:col-span-5 space-y-2.5 max-h-[700px] overflow-y-auto pr-1">
            {filteredFindings.map((item, idx) => {
              const finding = item.finding;
              const statusBadge = getStatusBadge(item.status);
              const StatusIcon = statusBadge.icon;
              const sevStyle = getSeverityStyle(finding.severity as any);
              const isSelected = idx === selectedItemIndex;

              return (
                <button
                  key={`${item.status}-${idx}-${finding.scanner}-${finding.rule_id}`}
                  onClick={() => setSelectedItemIndex(idx)}
                  className={`w-full text-left p-3.5 rounded-xl border transition-all flex flex-col gap-2 ${
                    isSelected
                      ? "bg-surface-elevated border-primary/50 shadow-md shadow-primary/5"
                      : "bg-surface border-border hover:border-border-active"
                  }`}
                >
                  {/* Item Badges */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`flex items-center gap-1 text-[10px] font-mono font-bold px-2 py-0.5 rounded-md border uppercase ${statusBadge.badge}`}
                      >
                        <StatusIcon className="w-3 h-3" />
                        <span>{statusBadge.label}</span>
                      </span>

                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-md border uppercase ${sevStyle.badge}`}
                      >
                        {finding.severity}
                      </span>
                    </div>

                    <span className="text-[10px] font-mono text-text-muted">
                      {finding.scanner}
                    </span>
                  </div>

                  {/* Title */}
                  <h4 className="text-xs font-bold font-mono text-text-primary line-clamp-2">
                    {finding.title}
                  </h4>

                  {/* File & Line */}
                  <div className="flex items-center gap-1 text-[11px] font-mono text-text-muted truncate">
                    <FileCode className="w-3 h-3 text-text-muted shrink-0" />
                    <span className="truncate">
                      {finding.file_path || (finding as any).file || "unknown"}
                      {finding.line_number || (finding as any).line ? `:${finding.line_number || (finding as any).line}` : ""}
                    </span>
                  </div>

                  {/* Change Details */}
                  {item.changeDetails && (
                    <div className="text-[10px] font-mono text-purple-400 flex items-center gap-1 mt-0.5">
                      <span>{item.changeDetails}</span>
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Finding Detail (Right column) */}
          <div className="lg:col-span-7">
            {selectedItem && (
              <div className="space-y-4">
                {/* Status Notice Banner above detail */}
                {selectedItem.status === "fixed" && (
                  <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                    <div>
                      <h4 className="text-xs font-bold font-mono text-emerald-400">
                        Finding Successfully Resolved
                      </h4>
                      <p className="text-[11px] font-mono text-text-primary mt-0.5">
                        This vulnerability or defect was detected in the previous scan and is no longer present in the re-scan.
                      </p>
                    </div>
                  </div>
                )}

                {selectedItem.status === "new" && (
                  <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
                    <div>
                      <h4 className="text-xs font-bold font-mono text-rose-400">
                        New Finding Introduced
                      </h4>
                      <p className="text-[11px] font-mono text-text-primary mt-0.5">
                        This issue was not present in the baseline scan. Review the changes introduced in this revision.
                      </p>
                    </div>
                  </div>
                )}

                {selectedItem.status === "changed" && (
                  <div className="p-4 rounded-xl border border-purple-500/30 bg-purple-500/10 flex items-center gap-3">
                    <RefreshCw className="w-5 h-5 text-purple-400 shrink-0" />
                    <div>
                      <h4 className="text-xs font-bold font-mono text-purple-400">
                        Finding Modified
                      </h4>
                      <p className="text-[11px] font-mono text-text-primary mt-0.5">
                        {selectedItem.changeDetails || "Finding properties modified between scans."}
                      </p>
                    </div>
                  </div>
                )}

                {/* Render the Finding Detail */}
                {(() => {
                  const targetFinding = selectedItem.finding;
                  const normalized: NormalizedFinding = {
                    ...targetFinding,
                    file_path: targetFinding.file_path || (targetFinding as any).file || "unknown",
                    line_number: targetFinding.line_number || (targetFinding as any).line || 1,
                  };

                  return (
                    <FindingDetail
                      finding={normalized}
                      comparisonStatus={selectedItem.status}
                      previousFinding={selectedItem.previousFinding}
                      changeDetails={selectedItem.changeDetails}
                    />
                  );
                })()}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
