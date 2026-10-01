export const SCORING_PILLARS = [
  { key: "security", name: "Security", weight: "30%", description: "Secret exposure, injection risks, CVEs, insecure configs" },
  { key: "reliability", name: "Reliability", weight: "25%", description: "Runtime bugs, uncaught errors, memory issues" },
  { key: "code_quality", name: "Code Quality", weight: "15%", description: "Complexity, dead code, maintainability antipatterns" },
  { key: "performance", name: "Performance", weight: "10%", description: "Resource utilization, memory leaks, algorithmic bottlenecks" },
  { key: "architecture", name: "Architecture", weight: "10%", description: "Modular coupling, circular dependencies, directory layout" },
  { key: "completeness", name: "Completeness", weight: "10%", description: "README, .gitignore, .env.example, license, tests" },
] as const;

export const SCANNING_STEPS = [
  { id: "acquire", label: "Acquiring project repository / archive", icon: "Download" },
  { id: "discover", label: "Inspecting language structure & manifests", icon: "Search" },
  { id: "static", label: "Executing multi-scanner static analysis", icon: "Cpu" },
  { id: "security", label: "Auditing secrets, CVEs, and injection risks", icon: "Shield" },
  { id: "ai", label: "Synthesizing AI context & fix remediation", icon: "Sparkles" },
  { id: "score", label: "Calculating deterministic 6-pillar score", icon: "Calculator" },
] as const;
