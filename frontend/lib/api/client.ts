/**
 * Dr.RopoSky Backend API client.
 */

import type { AnalysisReport, APIErrorResponse, HealthResponse, ComparisonReport } from "@/types/report";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class APIError extends Error {
  code: string;
  status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "APIError";
    this.code = code;
    this.status = status;
  }
}

async function handleResponseError(
  response: Response,
  defaultCode: string,
  defaultAction: string
): Promise<never> {
  let errorCode = defaultCode;
  let errorMessage = `${defaultAction} failed with HTTP status ${response.status}${
    response.statusText ? ` (${response.statusText})` : ""
  }`;

  try {
    const text = await response.text();
    if (text && text.trim()) {
      try {
        const json = JSON.parse(text);
        if (json && typeof json === "object") {
          if (json.error && typeof json.error === "object") {
            errorCode = json.error.code || errorCode;
            errorMessage = json.error.message || errorMessage;
          } else if (json.detail) {
            if (typeof json.detail === "object" && json.detail.message) {
              errorCode = json.detail.code || errorCode;
              errorMessage = json.detail.message;
            } else if (typeof json.detail === "string") {
              errorMessage = json.detail;
            }
          } else if (json.message) {
            errorMessage = json.message;
          }
        }
      } catch {
        // Plain text error response from server or proxy
        const trimmed = text.trim();
        errorMessage = trimmed.length > 250 ? `${trimmed.slice(0, 250)}...` : trimmed;
      }
    }
  } catch {
    // If reading body fails, use HTTP status message
  }

  throw new APIError(errorCode, errorMessage, response.status);
}

async function safeParseJson(response: Response, actionName: string): Promise<any> {
  let text = "";
  try {
    text = await response.text();
  } catch (err: any) {
    throw new APIError(
      "READ_ERROR",
      `Failed to read response stream for ${actionName}: ${err.message || "stream closed"}`,
      response.status
    );
  }

  if (!text || !text.trim()) {
    return {};
  }

  try {
    return JSON.parse(text);
  } catch (err: any) {
    throw new APIError(
      "PARSE_ERROR",
      `Response parsing error for ${actionName}: ${err.message}`,
      response.status
    );
  }
}

export async function checkHealth(): Promise<HealthResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/v1/health`, {
      method: "GET",
      headers: { Accept: "application/json" },
    });
  } catch (err: any) {
    throw new APIError(
      "CONNECTION_ERROR",
      `Failed to connect to backend at ${API_BASE_URL}: ${err.message || "Network unreachable"}`,
      0
    );
  }

  if (!res.ok) {
    await handleResponseError(res, "HEALTH_CHECK_FAILED", "Health check");
  }

  return await safeParseJson(res, "health check");
}

function normalizeFinding(f: any): any {
  if (!f || typeof f !== "object") return f;
  const filePath = f.file_path || f.file || "";
  const lineNum =
    f.line_number !== undefined && f.line_number !== null
      ? f.line_number
      : f.line !== undefined && f.line !== null
      ? f.line
      : null;
  const colNum =
    f.column_number !== undefined && f.column_number !== null
      ? f.column_number
      : f.column !== undefined && f.column !== null
      ? f.column
      : null;

  let enrichment = f.enrichment;
  if (enrichment && typeof enrichment === "object") {
    let confScore: number = 0.8;
    if (typeof enrichment.confidence_score === "number") {
      confScore = enrichment.confidence_score;
    } else if (typeof enrichment.confidence === "number") {
      confScore = enrichment.confidence;
    } else if (typeof enrichment.confidence === "string") {
      const lower = enrichment.confidence.toLowerCase();
      confScore = lower === "high" ? 0.95 : lower === "medium" ? 0.8 : 0.6;
    }

    const diff =
      enrichment.suggested_code_diff ||
      (enrichment.code_before && enrichment.code_after
        ? `- ${enrichment.code_before}\n+ ${enrichment.code_after}`
        : enrichment.code_before
        ? `- ${enrichment.code_before}`
        : enrichment.code_after
        ? `+ ${enrichment.code_after}`
        : null);

    enrichment = {
      ...enrichment,
      explanation: enrichment.explanation || enrichment.why_it_matters || "",
      why_it_matters: enrichment.why_it_matters || enrichment.explanation || "",
      confidence_score: confScore,
      suggested_code_diff: diff,
    };
  }

  return {
    ...f,
    file: filePath,
    file_path: filePath,
    line: lineNum,
    line_number: lineNum,
    column: colNum,
    column_number: colNum,
    enrichment,
  };
}

function normalizeReport(data: any): AnalysisReport {
  if (!data || typeof data !== "object") return data;
  const project = data.project || {
    name: "Unknown Project",
    source_type: "git",
    languages: [],
    manifests: [],
  };
  const analysis = data.analysis || {
    started_at: new Date().toISOString(),
    duration_ms: 0,
    files_analyzed: 0,
  };
  const scanners = Array.isArray(data.scanners) ? data.scanners : [];
  const findings = Array.isArray(data.findings)
    ? data.findings.map(normalizeFinding)
    : [];
  const summary = data.summary || {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    info: 0,
  };
  const category_summary = data.category_summary || {
    bug: 0,
    security: 0,
    performance: 0,
    quality: 0,
    missing_essential: 0,
    architecture: 0,
  };

  return {
    ...data,
    project: {
      ...project,
      languages: Array.isArray(project.languages) ? project.languages : [],
      manifests: Array.isArray(project.manifests) ? project.manifests : [],
    },
    analysis,
    scanners,
    findings,
    summary,
    category_summary,
    project_id: data.project_id || undefined,
    scan_id: data.scan_id || undefined,
  };
}

export async function analyzeRepository(
  githubUrl?: string,
  zipFile?: File
): Promise<AnalysisReport> {
  const formData = new FormData();

  if (githubUrl) {
    formData.append("github_url", githubUrl.trim());
  } else if (zipFile) {
    formData.append("zip_file", zipFile);
  } else {
    throw new APIError(
      "INVALID_SOURCE",
      "Please provide a GitHub URL or a ZIP archive.",
      400
    );
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
      method: "POST",
      body: formData,
    });
  } catch (err: any) {
    throw new APIError(
      "NETWORK_ERROR",
      `Failed to connect to backend at ${API_BASE_URL}: ${err.message || "Network unreachable"}`,
      0
    );
  }

  if (!response.ok) {
    await handleResponseError(response, "ANALYSIS_FAILED", "Audit analysis");
  }

  const data = await safeParseJson(response, "audit report");

  try {
    return normalizeReport(data);
  } catch (err: any) {
    throw new APIError(
      "NORMALIZATION_ERROR",
      `Response normalization error: ${err.message || "Invalid report format"}`,
      response.status
    );
  }
}

export async function compareReports(
  previousReport: AnalysisReport,
  currentReport: AnalysisReport
): Promise<ComparisonReport> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/compare`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        previous_report: previousReport,
        current_report: currentReport,
      }),
    });
  } catch (err: any) {
    throw new APIError(
      "NETWORK_ERROR",
      `Failed to connect to backend at ${API_BASE_URL}: ${err.message || "Network unreachable"}`,
      0
    );
  }

  if (!response.ok) {
    await handleResponseError(response, "COMPARISON_FAILED", "Report comparison");
  }

  const data = await safeParseJson(response, "comparison report");

  if (data && typeof data === "object") {
    if (Array.isArray(data.fixed_findings)) {
      data.fixed_findings = data.fixed_findings.map(normalizeFinding);
    }
    if (Array.isArray(data.new_findings)) {
      data.new_findings = data.new_findings.map(normalizeFinding);
    }
    if (Array.isArray(data.remaining_findings)) {
      data.remaining_findings = data.remaining_findings.map(normalizeFinding);
    }
    if (Array.isArray(data.changed_findings)) {
      data.changed_findings = data.changed_findings.map((item: any) => ({
        ...item,
        finding: normalizeFinding(item.finding),
        previous_finding: item.previous_finding
          ? normalizeFinding(item.previous_finding)
          : null,
      }));
    }
  }

  return data as ComparisonReport;
}

export interface RescanResponse {
  project: any;
  previous_scan_id: string;
  current_scan_id: string;
  current_report: AnalysisReport;
  comparison: ComparisonReport;
}

export interface ProjectScanSummary {
  id: string;
  project_id: string;
  status: string;
  overall_score: number;
  security_score: number;
  reliability_score: number;
  quality_score: number;
  performance_score: number;
  architecture_score: number;
  completeness_score: number;
  total_findings: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  created_at: string;
}

export async function rescanProject(projectId: string): Promise<RescanResponse> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/v1/projects/${encodeURIComponent(projectId)}/rescan`,
      {
        method: "POST",
        headers: { Accept: "application/json" },
      }
    );
  } catch (err: any) {
    throw new APIError(
      "NETWORK_ERROR",
      `Failed to connect to backend at ${API_BASE_URL}: ${err.message || "Network unreachable"}`,
      0
    );
  }

  if (!response.ok) {
    await handleResponseError(response, "RESCAN_FAILED", "Project re-scan");
  }

  const data = await safeParseJson(response, "rescan response");
  const current_report = normalizeReport(data.current_report);
  const comparison = data.comparison;

  if (comparison && typeof comparison === "object") {
    if (Array.isArray(comparison.fixed_findings)) {
      comparison.fixed_findings = comparison.fixed_findings.map(normalizeFinding);
    }
    if (Array.isArray(comparison.new_findings)) {
      comparison.new_findings = comparison.new_findings.map(normalizeFinding);
    }
    if (Array.isArray(comparison.remaining_findings)) {
      comparison.remaining_findings = comparison.remaining_findings.map(normalizeFinding);
    }
    if (Array.isArray(comparison.changed_findings)) {
      comparison.changed_findings = comparison.changed_findings.map((item: any) => ({
        ...item,
        finding: normalizeFinding(item.finding),
        previous_finding: item.previous_finding
          ? normalizeFinding(item.previous_finding)
          : null,
      }));
    }
  }

  return {
    ...data,
    current_report,
    comparison,
  };
}

export async function getProjectScans(
  projectId: string,
  limit: number = 20
): Promise<ProjectScanSummary[]> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/v1/projects/${encodeURIComponent(projectId)}/scans?limit=${limit}`,
      {
        method: "GET",
        headers: { Accept: "application/json" },
      }
    );
  } catch (err: any) {
    throw new APIError(
      "NETWORK_ERROR",
      `Failed to connect to backend at ${API_BASE_URL}: ${err.message || "Network unreachable"}`,
      0
    );
  }

  if (!response.ok) {
    await handleResponseError(response, "RETRIEVE_SCANS_FAILED", "Project scan history");
  }

  const data = await safeParseJson(response, "project scan history");
  return Array.isArray(data) ? data : [];
}

export async function getScanComparison(scanId: string): Promise<ComparisonReport> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/v1/scans/${encodeURIComponent(scanId)}/comparison`,
      {
        method: "GET",
        headers: { Accept: "application/json" },
      }
    );
  } catch (err: any) {
    throw new APIError(
      "NETWORK_ERROR",
      `Failed to connect to backend at ${API_BASE_URL}: ${err.message || "Network unreachable"}`,
      0
    );
  }

  if (!response.ok) {
    await handleResponseError(response, "RETRIEVE_COMPARISON_FAILED", "Scan comparison");
  }

  const data = await safeParseJson(response, "scan comparison");
  const comparison = data.raw_comparison || data;
  if (comparison && typeof comparison === "object") {
    if (Array.isArray(comparison.fixed_findings)) {
      comparison.fixed_findings = comparison.fixed_findings.map(normalizeFinding);
    }
    if (Array.isArray(comparison.new_findings)) {
      comparison.new_findings = comparison.new_findings.map(normalizeFinding);
    }
    if (Array.isArray(comparison.remaining_findings)) {
      comparison.remaining_findings = comparison.remaining_findings.map(normalizeFinding);
    }
    if (Array.isArray(comparison.changed_findings)) {
      comparison.changed_findings = comparison.changed_findings.map((item: any) => ({
        ...item,
        finding: normalizeFinding(item.finding),
        previous_finding: item.previous_finding
          ? normalizeFinding(item.previous_finding)
          : null,
      }));
    }
  }

  return comparison as ComparisonReport;
}

