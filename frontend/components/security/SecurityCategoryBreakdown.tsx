"use client";

import React from "react";
import { NormalizedFinding } from "@/types/report";
import { KeyRound, ShieldAlert, Package, Lock } from "lucide-react";

interface SecurityCategoryBreakdownProps {
  findings: NormalizedFinding[];
  selectedSubcategory: string;
  onSelectSubcategory: (sub: string) => void;
}

export const SecurityCategoryBreakdown: React.FC<SecurityCategoryBreakdownProps> = ({
  findings,
  selectedSubcategory,
  onSelectSubcategory,
}) => {
  // Classify security findings into authentic subcategories
  const isSecret = (f: NormalizedFinding) => {
    const scanner = f.scanner || "";
    const title = (f.title || "").toLowerCase();
    return (
      scanner.includes("secret") ||
      scanner === "gitleaks" ||
      title.includes("secret") ||
      title.includes("key") ||
      title.includes("token") ||
      title.includes("password")
    );
  };

  const isDependency = (f: NormalizedFinding) => {
    const scanner = f.scanner || "";
    const title = (f.title || "").toLowerCase();
    return (
      scanner === "npm-audit" ||
      scanner === "pip-audit" ||
      title.includes("dependency") ||
      title.includes("package") ||
      title.includes("cve")
    );
  };

  const isInjection = (f: NormalizedFinding) => {
    const scanner = f.scanner || "";
    const title = (f.title || "").toLowerCase();
    return (
      title.includes("injection") ||
      title.includes("eval") ||
      title.includes("exec") ||
      title.includes("deserialization") ||
      scanner === "bandit" ||
      scanner === "semgrep"
    );
  };

  const safeFindings = findings || [];
  const secretsCount = safeFindings.filter(isSecret).length;
  const depCount = safeFindings.filter(isDependency).length;
  const injectionCount = safeFindings.filter((f) => isInjection(f) && !isSecret(f) && !isDependency(f)).length;
  const configCount = safeFindings.filter((f) => !isSecret(f) && !isDependency(f) && !isInjection(f)).length;

  const subcats = [
    { id: "all", label: "All Security", count: safeFindings.length, icon: Lock },
    { id: "secrets", label: "Hardcoded Secrets & Keys", count: secretsCount, icon: KeyRound },
    { id: "injection", label: "Injection & AST Vulnerabilities", count: injectionCount, icon: ShieldAlert },
    { id: "dependencies", label: "Dependency & Supply Chain", count: depCount, icon: Package },
    { id: "config", label: "Insecure Config & Auth", count: configCount, icon: Lock },
  ];

  return (
    <div className="flex flex-wrap items-center gap-2 mb-6">
      {subcats.map((cat) => {
        const Icon = cat.icon;
        const isSelected = selectedSubcategory === cat.id;

        return (
          <button
            key={cat.id}
            onClick={() => onSelectSubcategory(cat.id)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-mono transition-all border ${
              isSelected
                ? "bg-surface-elevated text-text-primary border-primary/50 font-semibold shadow-sm"
                : "bg-surface/50 text-text-secondary border-border hover:border-border-active hover:bg-surface"
            }`}
          >
            <Icon className={`w-3.5 h-3.5 ${isSelected ? "text-primary" : "text-text-muted"}`} />
            <span>{cat.label}</span>
            <span
              className={`px-1.5 py-0.2 rounded text-[10px] ${
                isSelected ? "bg-primary/20 text-primary" : "bg-surface-elevated text-text-muted"
              }`}
            >
              {cat.count}
            </span>
          </button>
        );
      })}
    </div>
  );
};
