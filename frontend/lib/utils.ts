import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { FindingCategory, SeverityLevel } from "@/types/report";



export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function formatDate(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
}

export function getRatingBandFromScore(score: number): string {
  if (score >= 80) return "Strong Baseline";
  if (score >= 60) return "Needs Improvement";
  if (score >= 40) return "Significant Issues";
  return "Severe Issues";
}

export function getRatingBandColor(band: string): {
  badge: string;
  text: string;
  border: string;
  bg: string;
} {
  switch (band?.toLowerCase()) {
    case "strong baseline":
      return {
        badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        text: "text-emerald-400",
        border: "border-emerald-500/30",
        bg: "from-emerald-500/10 to-transparent",
      };
    case "needs improvement":
      return {
        badge: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
        text: "text-cyan-400",
        border: "border-cyan-500/30",
        bg: "from-cyan-500/10 to-transparent",
      };
    case "significant issues":
      return {
        badge: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        text: "text-amber-400",
        border: "border-amber-500/30",
        bg: "from-amber-500/10 to-transparent",
      };
    case "severe issues":
    default:
      return {
        badge: "bg-rose-500/10 text-rose-400 border-rose-500/20",
        text: "text-rose-400",
        border: "border-rose-500/30",
        bg: "from-rose-500/10 to-transparent",
      };
  }
}

export function getSeverityStyle(severity: SeverityLevel): {
  badge: string;
  dot: string;
  text: string;
  border: string;
} {
  switch (severity?.toLowerCase()) {
    case "critical":
      return {
        badge: "bg-red-500/10 text-red-400 border-red-500/30",
        dot: "bg-red-500",
        text: "text-red-400",
        border: "border-red-500/30",
      };
    case "high":
      return {
        badge: "bg-orange-500/10 text-orange-400 border-orange-500/30",
        dot: "bg-orange-500",
        text: "text-orange-400",
        border: "border-orange-500/30",
      };
    case "medium":
      return {
        badge: "bg-amber-500/10 text-amber-400 border-amber-500/30",
        dot: "bg-amber-500",
        text: "text-amber-400",
        border: "border-amber-500/30",
      };
    case "low":
      return {
        badge: "bg-blue-500/10 text-blue-400 border-blue-500/30",
        dot: "bg-blue-500",
        text: "text-blue-400",
        border: "border-blue-500/30",
      };
    case "info":
    default:
      return {
        badge: "bg-zinc-500/10 text-zinc-400 border-zinc-500/30",
        dot: "bg-zinc-400",
        text: "text-zinc-400",
        border: "border-zinc-500/30",
      };
  }
}

export function getCategoryLabel(category: FindingCategory | string): string {
  const map: Record<string, string> = {
    bug: "Reliability & Bugs",
    security: "Security & Vulnerabilities",
    performance: "Performance",
    quality: "Code Quality",
    missing_essential: "Completeness & Essentials",
    architecture: "Architecture & Design",
  };
  return map[category] || category;
}

export function formatDelta(delta: number): string {
  if (delta > 0) return `+${delta}`;
  return `${delta}`;
}

export function formatScannerName(scanner: string): string {
  if (!scanner) return "Standard Scanner";
  const map: Record<string, string> = {
    "rokospy-secret-scanner": "Dr.RopoSky Secret Scanner",
    "rokospy-security-intelligence": "Dr.RopoSky Security Intelligence",
    "rokospy-essentials": "Dr.RopoSky Essentials Scanner",
    "rokospy-project-intelligence": "Dr.RopoSky Project Intelligence",
    "rokospy-architecture": "Dr.RopoSky Architecture Intelligence",
    "rokospy-structure-intelligence": "Dr.RopoSky Structure Intelligence",
    "gitleaks": "Gitleaks",
    "bandit": "Bandit",
    "pip-audit": "Pip Audit",
    "npm-audit": "NPM Audit",
    "eslint": "ESLint",
    "ruff": "Ruff",
    "semgrep": "Semgrep",
  };

  if (map[scanner]) return map[scanner];

  // Handle any other rokospy/roposky prefixes dynamically
  if (scanner.startsWith("rokospy-") || scanner.startsWith("roposky-")) {
    const rawSuffix = scanner.replace(/^(rokospy|roposky)-/, "");
    const formattedSuffix = rawSuffix
      .split("-")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
    return `Dr.RopoSky ${formattedSuffix}`;
  }

  return scanner;
}

export function getDeltaStyle(delta: number): {
  text: string;
  badge: string;
  border: string;
  bg: string;
} {
  if (delta > 0) {
    return {
      text: "text-emerald-400",
      badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
      border: "border-emerald-500/30",
      bg: "bg-emerald-500/10",
    };
  } else if (delta < 0) {
    return {
      text: "text-rose-400",
      badge: "bg-rose-500/10 text-rose-400 border-rose-500/30",
      border: "border-rose-500/30",
      bg: "bg-rose-500/10",
    };
  } else {
    return {
      text: "text-text-muted",
      badge: "bg-surface-elevated text-text-muted border-border",
      border: "border-border",
      bg: "bg-surface",
    };
  }
}
