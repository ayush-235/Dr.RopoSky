"use client";

import React from "react";
import { ProjectScore, SeveritySummary } from "@/types/report";
import { getRatingBandColor } from "@/lib/utils";
import { Shield, ShieldAlert, KeyRound, Package, Lock, CheckCircle2 } from "lucide-react";

interface SecurityPostureProps {
  score?: ProjectScore | null;
  summary: SeveritySummary;
  securityFindingsCount: number;
  secretsCount: number;
  dependenciesCount: number;
}

export const SecurityPosture: React.FC<SecurityPostureProps> = ({
  score,
  summary,
  securityFindingsCount,
  secretsCount,
  dependenciesCount,
}) => {
  // Authoritative Security score from backend (DO NOT recalculate)
  const securityScore =
    score?.categories?.security?.score ??
    score?.security ??
    (securityFindingsCount === 0 ? 100 : 0);

  const deductions = score?.categories?.security?.deductions ?? 0;
  const explanation =
    score?.categories?.security?.explanation ||
    (securityFindingsCount === 0
      ? "No security findings were reported by the static/security scanners."
      : "Deductions based on detected security vulnerabilities.");

  const getScoreBadge = (val: number) => {
    if (val >= 80)
      return {
        badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
        text: "text-emerald-400",
        label: "Secure Baseline",
      };
    if (val >= 60)
      return {
        badge: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
        text: "text-cyan-400",
        label: "Moderate Risk",
      };
    if (val >= 40)
      return {
        badge: "bg-amber-500/10 text-amber-400 border-amber-500/30",
        text: "text-amber-400",
        label: "Elevated Risk",
      };
    return {
      badge: "bg-red-500/10 text-red-400 border-red-500/30",
      text: "text-red-400",
      label: "Critical Threat Posture",
    };
  };

  const badge = getScoreBadge(securityScore);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
      {/* Security Posture Index */}
      <div className="col-span-1 lg:col-span-2 p-6 rounded-xl border border-border bg-gradient-to-br from-surface to-surface-elevated/80 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-mono font-bold text-text-primary uppercase tracking-wider">
                Security Pillar Posture
              </h3>
              <span className="text-[11px] font-mono text-text-muted">
                Authoritative Deterministic Index (Weight: 30%)
              </span>
            </div>
          </div>
          <span
            className={`text-xs font-mono font-semibold px-2.5 py-1 rounded-full border ${badge.badge}`}
          >
            {badge.label}
          </span>
        </div>

        <div className="my-5 flex items-baseline gap-3">
          <span className={`text-5xl font-bold font-mono ${badge.text}`}>
            {securityScore}
          </span>
          <span className="text-lg font-mono text-text-muted">/ 100</span>
          {deductions > 0 && (
            <span className="text-xs font-mono text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
              -{deductions} pts deducted
            </span>
          )}
        </div>

        <p className="text-xs font-mono text-text-secondary leading-relaxed border-t border-border pt-3">
          {explanation}
        </p>
      </div>

      {/* Quick Security Metrics Card 1: Secrets & Injection */}
      <div className="p-5 rounded-xl border border-border bg-surface/60 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-text-secondary uppercase tracking-wider">
            Exposed Credentials
          </span>
          <KeyRound className="w-4 h-4 text-red-400" />
        </div>
        <div className="my-3">
          <span className="text-3xl font-bold font-mono text-text-primary">
            {secretsCount}
          </span>
          <span className="text-xs font-mono text-text-muted ml-1.5">
            detected
          </span>
        </div>
        <div className="text-[11px] font-mono text-text-muted flex items-center gap-1.5">
          <Lock className="w-3 h-3 text-emerald-400" />
          <span>Redaction Active</span>
        </div>
      </div>

      {/* Quick Security Metrics Card 2: Dependencies & Vulnerabilities */}
      <div className="p-5 rounded-xl border border-border bg-surface/60 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-text-secondary uppercase tracking-wider">
            Dependency Advisories
          </span>
          <Package className="w-4 h-4 text-amber-400" />
        </div>
        <div className="my-3">
          <span className="text-3xl font-bold font-mono text-text-primary">
            {dependenciesCount}
          </span>
          <span className="text-xs font-mono text-text-muted ml-1.5">
            CVE packages
          </span>
        </div>
        <div className="text-[11px] font-mono text-text-muted flex items-center gap-1.5">
          <CheckCircle2 className="w-3 h-3 text-primary" />
          <span>Lockfile static audit</span>
        </div>
      </div>
    </div>
  );
};
