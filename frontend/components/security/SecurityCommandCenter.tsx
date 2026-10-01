"use client";

import React, { useState, useMemo } from "react";
import { AnalysisReport, NormalizedFinding } from "@/types/report";
import { SecurityPosture } from "./SecurityPosture";
import { SecuritySeverityBreakdown } from "./SecuritySeverityBreakdown";
import { SecurityScannerCoverage } from "./SecurityScannerCoverage";
import { SecurityCategoryBreakdown } from "./SecurityCategoryBreakdown";
import { SecurityFindingsExplorer } from "./SecurityFindingsExplorer";
import { Shield, Lock } from "lucide-react";

interface SecurityCommandCenterProps {
  report: AnalysisReport;
}

export const SecurityCommandCenter: React.FC<SecurityCommandCenterProps> = ({
  report,
}) => {
  const [selectedSubcategory, setSelectedSubcategory] = useState<string>("all");

  // Extract all security-relevant findings from authoritative report
  const securityFindings: NormalizedFinding[] = useMemo(() => {
    return report.findings.filter((f) => {
      // Direct category is security
      if (f.category === "security") return true;

      // Or security scanners
      if (
        f.scanner === "rokospy-secret-scanner" ||
        f.scanner === "gitleaks" ||
        f.scanner === "npm-audit" ||
        f.scanner === "pip-audit" ||
        f.scanner === "bandit"
      ) {
        return true;
      }

      // Or security keywords in title/rule
      const titleLower = f.title.toLowerCase();
      if (
        titleLower.includes("injection") ||
        titleLower.includes("secret") ||
        titleLower.includes("credential") ||
        titleLower.includes("vulnerability")
      ) {
        return true;
      }

      return false;
    });
  }, [report.findings]);

  // Compute specific counts
  const secretsCount = useMemo(() => {
    return securityFindings.filter(
      (f) =>
        f.scanner.includes("secret") ||
        f.scanner === "gitleaks" ||
        f.title.toLowerCase().includes("secret") ||
        f.title.toLowerCase().includes("key") ||
        f.title.toLowerCase().includes("token")
    ).length;
  }, [securityFindings]);

  const dependenciesCount = useMemo(() => {
    return securityFindings.filter(
      (f) =>
        f.scanner === "npm-audit" ||
        f.scanner === "pip-audit" ||
        f.title.toLowerCase().includes("dependency") ||
        f.title.toLowerCase().includes("package")
    ).length;
  }, [securityFindings]);

  return (
    <div className="w-full space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border border-red-500/20 bg-red-500/5">
        <div className="flex items-center gap-2.5 text-text-primary">
          <div className="w-7 h-7 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-text-primary">
              Cybersecurity Command Center
            </h2>
            <p className="text-[11px] font-mono text-text-muted">
              Live threat vector analysis, AST vulnerabilities, secrets telemetry & dependency audit
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-emerald-400">
          <Lock className="w-3.5 h-3.5" />
          <span>ZERO CODE EXECUTION ACTIVE</span>
        </div>
      </div>

      {/* Security Posture Index */}
      <SecurityPosture
        score={report.score}
        summary={report.summary}
        securityFindingsCount={securityFindings.length}
        secretsCount={secretsCount}
        dependenciesCount={dependenciesCount}
      />

      {/* Severity Triage Breakdown & Scanner Telemetry Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <SecuritySeverityBreakdown findings={securityFindings} />
        </div>
        <div className="lg:col-span-5">
          <SecurityScannerCoverage scanners={report.scanners} />
        </div>
      </div>

      {/* Subcategory Filter Tabs */}
      <SecurityCategoryBreakdown
        findings={securityFindings}
        selectedSubcategory={selectedSubcategory}
        onSelectSubcategory={setSelectedSubcategory}
      />

      {/* Security Findings Explorer */}
      <SecurityFindingsExplorer
        findings={securityFindings}
        selectedSubcategory={selectedSubcategory}
      />
    </div>
  );
};
