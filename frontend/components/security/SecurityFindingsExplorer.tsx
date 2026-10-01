"use client";

import React, { useState, useMemo } from "react";
import { NormalizedFinding } from "@/types/report";
import { getSeverityStyle, formatScannerName } from "@/lib/utils";
import { FindingDetail } from "../findings/FindingDetail";
import { Search, ChevronRight, CheckCircle2, Sparkles, Lock, KeyRound } from "lucide-react";

interface SecurityFindingsExplorerProps {
  findings: NormalizedFinding[];
  selectedSubcategory: string;
}

export const SecurityFindingsExplorer: React.FC<SecurityFindingsExplorerProps> = ({
  findings,
  selectedSubcategory,
}) => {
  const [selectedSeverity, setSelectedSeverity] = useState<string>("all");
  const [selectedScanner, setSelectedScanner] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedFindingId, setSelectedFindingId] = useState<string>(
    findings[0]?.id || ""
  );

  const severities = [
    { id: "all", label: "All Severities" },
    { id: "critical", label: "Critical" },
    { id: "high", label: "High" },
    { id: "medium", label: "Medium" },
    { id: "low", label: "Low" },
    { id: "info", label: "Info" },
  ];

  // Available scanners in this finding set
  const availableScanners = useMemo(() => {
    const list = Array.from(new Set(findings.map((f) => f.scanner)));
    return ["all", ...list];
  }, [findings]);

  // Subcategory classifier
  const matchesSubcategory = (f: NormalizedFinding, subcat: string) => {
    if (subcat === "all") return true;

    const isSecret =
      f.scanner.includes("secret") ||
      f.scanner === "gitleaks" ||
      f.title.toLowerCase().includes("secret") ||
      f.title.toLowerCase().includes("key") ||
      f.title.toLowerCase().includes("token") ||
      f.title.toLowerCase().includes("password");

    const isDependency =
      f.scanner === "npm-audit" ||
      f.scanner === "pip-audit" ||
      f.title.toLowerCase().includes("dependency") ||
      f.title.toLowerCase().includes("package") ||
      f.title.toLowerCase().includes("cve");

    const isInjection =
      f.title.toLowerCase().includes("injection") ||
      f.title.toLowerCase().includes("eval") ||
      f.title.toLowerCase().includes("exec") ||
      f.title.toLowerCase().includes("deserialization") ||
      f.scanner === "bandit" ||
      f.scanner === "semgrep";

    if (subcat === "secrets") return isSecret;
    if (subcat === "dependencies") return isDependency;
    if (subcat === "injection") return isInjection && !isSecret && !isDependency;
    if (subcat === "config") return !isSecret && !isDependency && !isInjection;
    return true;
  };

  // Filtered list
  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      // Subcategory filter
      if (!matchesSubcategory(f, selectedSubcategory)) return false;

      // Severity filter
      if (selectedSeverity !== "all" && f.severity !== selectedSeverity)
        return false;

      // Scanner filter
      if (selectedScanner !== "all" && f.scanner !== selectedScanner)
        return false;

      // Search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const filePath = f.file_path || f.file || "";
        return (
          (f.title || "").toLowerCase().includes(q) ||
          (f.message || "").toLowerCase().includes(q) ||
          filePath.toLowerCase().includes(q) ||
          (f.scanner || "").toLowerCase().includes(q) ||
          Boolean(f.rule_id?.toLowerCase().includes(q))
        );
      }
      return true;
    });
  }, [findings, selectedSubcategory, selectedSeverity, selectedScanner, searchQuery]);

  const selectedFinding = useMemo(() => {
    return (
      filteredFindings.find((f) => f.id === selectedFindingId) ||
      filteredFindings[0] ||
      null
    );
  }, [filteredFindings, selectedFindingId]);

  return (
    <div className="w-full">
      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
        <div className="flex flex-wrap items-center gap-2">
          {/* Severity Badges */}
          <div className="flex items-center gap-1 p-1 rounded-lg bg-surface border border-border">
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

          {/* Scanner Filter */}
          {availableScanners.length > 2 && (
            <select
              value={selectedScanner}
              onChange={(e) => setSelectedScanner(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-surface border border-border text-xs font-mono text-text-secondary focus:outline-none focus:border-primary/60"
            >
              <option value="all">All Scanners</option>
              {availableScanners
                .filter((s) => s !== "all")
                .map((s) => (
                  <option key={s} value={s}>
                    {formatScannerName(s)}
                  </option>
                ))}
            </select>
          )}
        </div>

        {/* Search */}
        <div className="relative w-full md:w-64">
          <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search security findings..."
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-surface border border-border focus:border-primary/60 focus:outline-none text-xs font-mono text-text-primary placeholder:text-text-muted"
          />
        </div>
      </div>

      {/* Findings List & Detail Grid */}
      {filteredFindings.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Finding Cards */}
          <div className="lg:col-span-5 space-y-2.5 max-h-[680px] overflow-y-auto pr-1">
            {filteredFindings.map((f) => {
              const sev = getSeverityStyle(f.severity);
              const isSelected = selectedFinding?.id === f.id;

              return (
                <div
                  key={f.id}
                  onClick={() => setSelectedFindingId(f.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? "bg-surface border-red-500/50 shadow-md shadow-red-500/5"
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

                  <h4 className="text-xs font-bold font-mono text-text-primary line-clamp-1 mb-1">
                    {f.title}
                  </h4>

                  <div className="flex items-center justify-between text-[11px] font-mono text-text-muted">
                    <span className="truncate max-w-[200px]">
                      {f.file_path || f.file || "project"}
                      {f.line_number || f.line ? `:${f.line_number ?? f.line}` : ""}
                    </span>
                    <ChevronRight
                      className={`w-3.5 h-3.5 transition-transform ${
                        isSelected ? "text-primary translate-x-0.5" : ""
                      }`}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right Column: Detail View */}
          <div className="lg:col-span-7">
            {selectedFinding && <FindingDetail finding={selectedFinding} />}
          </div>
        </div>
      ) : (
        <div className="p-12 rounded-xl border border-border bg-surface/30 text-center flex flex-col items-center justify-center">
          <CheckCircle2 className="w-10 h-10 text-emerald-400 mb-3" />
          <h4 className="text-sm font-bold font-mono text-text-primary">
            No Security Findings Found
          </h4>
          <p className="text-xs font-mono text-text-muted mt-1 max-w-md">
            No security findings were reported by the available static/security scanners for the selected filters.
          </p>
        </div>
      )}
    </div>
  );
};
