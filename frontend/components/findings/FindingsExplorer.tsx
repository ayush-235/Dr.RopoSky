"use client";

import React, { useState, useMemo } from "react";
import { NormalizedFinding, SeverityLevel, FindingCategory } from "@/types/report";
import { getSeverityStyle, getCategoryLabel, formatScannerName } from "@/lib/utils";
import { FindingDetail } from "./FindingDetail";
import { Search, Filter, Shield, AlertTriangle, Bug, Sparkles, CheckCircle2, ChevronRight, FileCode } from "lucide-react";

interface FindingsExplorerProps {
  findings: NormalizedFinding[];
}

export const FindingsExplorer: React.FC<FindingsExplorerProps> = ({ findings }) => {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedFindingId, setSelectedFindingId] = useState<string>(
    findings[0]?.id || ""
  );

  const categories = [
    { id: "all", label: "All Categories" },
    { id: "security", label: "Security" },
    { id: "bug", label: "Reliability" },
    { id: "quality", label: "Quality" },
    { id: "performance", label: "Performance" },
    { id: "architecture", label: "Architecture" },
    { id: "missing_essential", label: "Completeness" },
  ];

  const severities = [
    { id: "all", label: "All Severities" },
    { id: "critical", label: "Critical" },
    { id: "high", label: "High" },
    { id: "medium", label: "Medium" },
    { id: "low", label: "Low" },
    { id: "info", label: "Info" },
  ];

  // Filter findings
  const filteredFindings = useMemo(() => {
    return (findings || []).filter((f) => {
      // Category filter
      if (selectedCategory !== "all" && f.category !== selectedCategory) {
        return false;
      }
      // Severity filter
      if (selectedSeverity !== "all" && f.severity !== selectedSeverity) {
        return false;
      }
      // Search filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesTitle = (f.title || "").toLowerCase().includes(query);
        const matchesMsg = (f.message || "").toLowerCase().includes(query);
        const filePath = f.file_path || f.file || "";
        const matchesFile = filePath.toLowerCase().includes(query);
        const matchesScanner = (f.scanner || "").toLowerCase().includes(query);
        const matchesRule = Boolean(f.rule_id?.toLowerCase().includes(query));
        return (
          matchesTitle ||
          matchesMsg ||
          matchesFile ||
          matchesScanner ||
          matchesRule
        );
      }
      return true;
    });
  }, [findings, selectedCategory, selectedSeverity, searchQuery]);

  const selectedFinding = useMemo(() => {
    return (
      filteredFindings.find((f) => f.id === selectedFindingId) ||
      filteredFindings[0] ||
      null
    );
  }, [filteredFindings, selectedFindingId]);

  return (
    <div className="w-full">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-sm font-bold font-mono text-text-primary uppercase tracking-wider">
            Audit Findings Explorer ({filteredFindings.length} of {findings.length})
          </h2>
          <p className="text-xs font-mono text-text-muted">
            Inspect static evidence, security risks, and AI remediation guides
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search findings, files, rules..."
            className="w-full pl-9 pr-3.5 py-1.5 rounded-lg bg-surface border border-border focus:border-primary/60 focus:outline-none text-xs font-mono text-text-primary placeholder:text-text-muted"
          />
        </div>
      </div>

      {/* Category & Severity Filter Bars */}
      <div className="flex flex-wrap items-center gap-2 mb-6">
        <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-lg bg-surface border border-border">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-all ${
                selectedCategory === cat.id
                  ? "bg-surface-elevated text-text-primary border border-border font-semibold shadow-sm"
                  : "text-text-muted hover:text-text-secondary"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-lg bg-surface border border-border">
          {severities.map((sev) => (
            <button
              key={sev.id}
              onClick={() => setSelectedSeverity(sev.id)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-all ${
                selectedSeverity === sev.id
                  ? "bg-surface-elevated text-text-primary border border-border font-semibold shadow-sm"
                  : "text-text-muted hover:text-text-secondary"
              }`}
            >
              {sev.label}
            </button>
          ))}
        </div>
      </div>

      {/* Findings List & Detail Grid */}
      {filteredFindings.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Findings List (Left column) */}
          <div className="lg:col-span-5 space-y-2.5 max-h-[720px] overflow-y-auto pr-1">
            {filteredFindings.map((f) => {
              const sev = getSeverityStyle(f.severity);
              const isSelected = selectedFinding?.id === f.id;

              return (
                <div
                  key={f.id}
                  onClick={() => setSelectedFindingId(f.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? "bg-surface border-primary/50 shadow-md shadow-primary/5"
                      : "bg-surface/40 hover:bg-surface border-border hover:border-border-active"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${sev.dot}`} />
                      <span className={`text-[11px] font-mono font-semibold uppercase ${sev.text}`}>
                        {f.severity}
                      </span>
                      <span className="text-[11px] font-mono text-text-muted">
                        &bull; {formatScannerName(f.scanner)}
                      </span>
                    </div>
                    {f.enrichment && (
                      <span className="flex items-center gap-1 text-[10px] font-mono text-accent-violet">
                        <Sparkles className="w-3 h-3" />
                        <span>AI</span>
                      </span>
                    )}
                  </div>

                  <h3 className="text-xs font-bold font-mono text-text-primary line-clamp-1 mb-1">
                    {f.title}
                  </h3>

                  <div className="flex items-center justify-between text-[11px] font-mono text-text-muted">
                    <span className="truncate max-w-[200px]">
                      {f.file_path || f.file || "project"}
                      {f.line_number || f.line ? `:${f.line_number ?? f.line}` : ""}
                    </span>
                    <ChevronRight className={`w-3.5 h-3.5 transition-transform ${isSelected ? "text-primary translate-x-0.5" : ""}`} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Finding Detail (Right column) */}
          <div className="lg:col-span-7">
            {selectedFinding && <FindingDetail finding={selectedFinding} />}
          </div>
        </div>
      ) : (
        <div className="p-12 rounded-xl border border-border bg-surface/30 text-center flex flex-col items-center justify-center">
          <CheckCircle2 className="w-10 h-10 text-emerald-400 mb-3" />
          <h3 className="text-sm font-bold font-mono text-text-primary">
            No Findings Matched
          </h3>
          <p className="text-xs font-mono text-text-muted mt-1 max-w-sm">
            No issues match the selected category, severity, or search filters.
          </p>
        </div>
      )}
    </div>
  );
};
