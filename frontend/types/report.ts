/**
 * TypeScript types matching Dr.RopoSky backend AnalysisReport and API schemas.
 */

export type SeverityLevel = "critical" | "high" | "medium" | "low" | "info";

export type FindingCategory =
  | "bug"
  | "security"
  | "performance"
  | "quality"
  | "missing_essential"
  | "architecture";

export type ScannerStatus = "success" | "failed" | "unavailable" | "skipped";

export interface ScannerExecutionResult {
  scanner: string;
  status: ScannerStatus;
  findings_count: number;
  duration_ms: number;
  error_message?: string | null;
}

export interface ProjectMetadata {
  name: string;
  source_type: string;
  languages: string[];
  manifests: string[];
  target_url?: string;
}

export interface AnalysisExecutionInfo {
  started_at: string;
  duration_ms: number;
  files_analyzed: number;
}

export interface SeveritySummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface CategorySummary {
  bug: number;
  security: number;
  performance: number;
  quality: number;
  missing_essential: number;
  architecture: number;
}

export interface AIContextData {
  relevant_lines: string;
  imports_in_scope: string[];
  enclosing_function?: string | null;
  enclosing_class?: string | null;
}

export interface AIFindingEnrichment {
  explanation?: string;
  why_it_matters?: string;
  impact?: string;
  fix_steps?: string[];
  suggested_code_diff?: string | null;
  code_before?: string;
  code_after?: string;
  confidence?: string | number;
  confidence_score?: number;
  status?: string;
  error_message?: string | null;
}

export interface NormalizedFinding {
  id: string;
  title: string;
  message: string;
  severity: SeverityLevel;
  category: FindingCategory;
  scanner: string;
  file?: string;
  file_path?: string;
  line?: number | null;
  line_number?: number | null;
  column?: number | null;
  column_number?: number | null;
  evidence?: string | null;
  confidence?: string;
  source?: string;
  fingerprint: string;
  rule_id?: string | null;
  enrichment?: AIFindingEnrichment | null;
}

export interface AIExecutionSummary {
  findings_enriched: number;
  model_used: string;
  provider: string;
  total_duration_ms: number;
}

export interface CategoryScore {
  category: string;
  score: number;
  finding_count: number;
  deductions: number;
  explanation: string;
}

export interface ProjectScore {
  overall: number;
  rating_band: string;
  security: number;
  reliability: number;
  code_quality: number;
  performance: number;
  architecture: number;
  completeness: number;
  categories: Record<string, CategoryScore>;
}

export interface RouteInfo {
  method: string;
  path: string;
  file: string;
  line: number;
  has_validation: boolean;
  has_auth?: boolean;
  has_role_check?: boolean;
  has_ownership_check?: boolean;
  is_sensitive?: boolean;
  is_admin?: boolean;
  is_payment?: boolean;
  handler_name?: string | null;
}

export interface ProjectIntelligence {
  project_type: string;
  frameworks: string[];
  entry_points: string[];
  routes_detected: RouteInfo[];
  env_vars_used: string[];
  env_vars_documented: string[];
  missing_env_vars: string[];
  direct_dependencies: string[];
  has_lockfile: boolean;
  lockfile_names: string[];
  has_tests: boolean;
  test_frameworks: string[];
  test_files_count: number;
  db_orm_detected: string[];
  auth_mechanisms_detected: string[];
  has_global_auth?: boolean;
  god_modules?: string[];
  scattered_config_files?: string[];
  layer_violations?: string[];
}


export interface PillarCoverage {
  pillar: string;
  coverage_pct: number;
  verifiable_aspects: string[];
  unverified_aspects: string[];
}

export interface AnalysisCoverage {
  overall_coverage_pct: number;
  pillars: Record<string, PillarCoverage>;
  evaluation_summary: string;
}

export interface AnalysisReport {
  schema_version: string;
  project: ProjectMetadata;
  analysis: AnalysisExecutionInfo;
  scanners: ScannerExecutionResult[];
  findings: NormalizedFinding[];
  summary: SeveritySummary;
  category_summary: CategorySummary;
  ai_summary?: AIExecutionSummary | null;
  score?: ProjectScore | null;
  coverage?: AnalysisCoverage | null;
  intelligence?: ProjectIntelligence | null;
  project_id?: string;
  scan_id?: string;
}


export interface APIErrorDetail {
  code: string;
  message: string;
}

export interface APIErrorResponse {
  error: APIErrorDetail;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface ScoreDelta {
  previous: number;
  current: number;
  delta: number;
}

export interface PillarsDelta {
  security: ScoreDelta;
  reliability: ScoreDelta;
  code_quality: ScoreDelta;
  performance: ScoreDelta;
  architecture: ScoreDelta;
  completeness: ScoreDelta;
}

export type FindingChangeStatus = "fixed" | "new" | "remaining" | "changed";

export interface FindingComparisonItem {
  status: FindingChangeStatus;
  finding: NormalizedFinding;
  previous_finding?: NormalizedFinding | null;
  change_details?: string | null;
}

export interface ComparisonSummary {
  fixed_count: number;
  new_count: number;
  remaining_count: number;
  changed_count: number;
  overall_delta: number;
  verdict: "improved" | "regressed" | "unchanged";
}

export interface ComparisonReport {
  schema_version: string;
  summary: ComparisonSummary;
  overall: ScoreDelta;
  pillars: PillarsDelta;
  fixed_findings: NormalizedFinding[];
  new_findings: NormalizedFinding[];
  remaining_findings: NormalizedFinding[];
  changed_findings: FindingComparisonItem[];
}

export type SceneState = "idle" | "input" | "scanning" | "issues" | "completed";

