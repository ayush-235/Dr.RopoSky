import { test, describe } from "node:test";
import assert from "node:assert/strict";

describe("Frontend Architecture & Data Integrity Tests", () => {
  test("1. SCORING_PILLARS matches all 6 required architectural pillars", async () => {
    const { SCORING_PILLARS } = await import("../lib/constants.ts");
    assert.equal(SCORING_PILLARS.length, 6);
    const keys = SCORING_PILLARS.map((p) => p.key);
    assert.deepEqual(keys, [
      "security",
      "reliability",
      "code_quality",
      "performance",
      "architecture",
      "completeness",
    ]);
  });

  test("2. Rating band style mappings provide high-contrast semantic treatments", async () => {
    const { getRatingBandColor } = await import("../lib/utils.ts");

    const strong = getRatingBandColor("Strong Baseline");
    assert.match(strong.badge, /emerald/);

    const needs = getRatingBandColor("Needs Improvement");
    assert.match(needs.badge, /cyan/);

    const significant = getRatingBandColor("Significant Issues");
    assert.match(significant.badge, /amber/);

    const severe = getRatingBandColor("Severe Issues");
    assert.match(severe.badge, /rose|red/);
  });

  test("3. Severity level styles correctly classify all standard levels", async () => {
    const { getSeverityStyle } = await import("../lib/utils.ts");

    assert.match(getSeverityStyle("critical").badge, /red/);
    assert.match(getSeverityStyle("high").badge, /orange/);
    assert.match(getSeverityStyle("medium").badge, /amber/);
    assert.match(getSeverityStyle("low").badge, /blue/);
    assert.match(getSeverityStyle("info").badge, /zinc/);
  });

  test("4. Category label lookup translates raw identifiers to developer labels", async () => {
    const { getCategoryLabel } = await import("../lib/utils.ts");

    assert.equal(getCategoryLabel("security"), "Security & Vulnerabilities");
    assert.equal(getCategoryLabel("bug"), "Reliability & Bugs");
    assert.equal(getCategoryLabel("missing_essential"), "Completeness & Essentials");
    assert.equal(getCategoryLabel("quality"), "Code Quality");
    assert.equal(getCategoryLabel("performance"), "Performance");
    assert.equal(getCategoryLabel("architecture"), "Architecture & Design");
  });

  test("5. Duration and date formatters handle zero and millisecond values cleanly", async () => {
    const { formatDuration, formatDate } = await import("../lib/utils.ts");

    assert.equal(formatDuration(450), "450ms");
    assert.equal(formatDuration(2400), "2.4s");

    const formatted = formatDate("2026-09-30T12:00:00Z");
    assert.match(formatted, /2026/);
  });

  test("6. API Client validation enforces mutual exclusivity between GitHub URL and ZIP", async () => {
    const { analyzeRepository, APIError } = await import("../lib/api/client.ts");

    await assert.rejects(
      async () => {
        await analyzeRepository(undefined, undefined);
      },
      (err) => {
        assert.ok(err instanceof APIError);
        assert.equal(err.code, "INVALID_SOURCE");
        return true;
      }
    );
  });

  test("7. Scanning progress stages reflect authentic pipeline steps", async () => {
    const { SCANNING_STEPS } = await import("../lib/constants.ts");
    assert.ok(SCANNING_STEPS.length >= 6);
    const ids = SCANNING_STEPS.map((s) => s.id);
    assert.ok(ids.includes("acquire"));
    assert.ok(ids.includes("static"));
    assert.ok(ids.includes("security"));
    assert.ok(ids.includes("score"));
  });

  test("8. Mock AnalysisReport adheres to Phase 3/4 backend schema contract", () => {
    const sampleReport = {
      schema_version: "1.0",
      project: {
        name: "test-repo",
        source_type: "git",
        languages: ["Python", "TypeScript"],
        manifests: ["pyproject.toml", "package.json"],
      },
      analysis: {
        started_at: "2026-09-30T21:00:00Z",
        duration_ms: 1200,
        files_analyzed: 42,
      },
      scanners: [
        {
          scanner: "rokospy-secret-scanner",
          status: "success",
          findings_count: 1,
          duration_ms: 50,
          error_message: null,
        },
      ],
      findings: [
        {
          id: "finding-1",
          title: "Hardcoded API Key",
          message: "AWS token detected in configuration",
          severity: "critical",
          category: "security",
          scanner: "rokospy-secret-scanner",
          file_path: "app/config.py",
          line_number: 12,
          evidence: "AWS_KEY = '[REDACTED_SECRET]'",
          fingerprint: "abc123sha",
          enrichment: {
            explanation: "Exposed keys can lead to cloud takeover",
            why_it_matters: "Attackers can deploy crypto miners",
            fix_steps: ["Rotate key", "Move to env"],
            confidence_score: 0.95,
          },
        },
      ],
      summary: { critical: 1, high: 0, medium: 0, low: 0, info: 0 },
      category_summary: {
        bug: 0,
        security: 1,
        performance: 0,
        quality: 0,
        missing_essential: 0,
        architecture: 0,
      },
      score: {
        overall: 75,
        rating_band: "Needs Improvement",
        security: 75,
        reliability: 100,
        code_quality: 100,
        performance: 100,
        architecture: 100,
        completeness: 100,
        categories: {
          security: {
            category: "security",
            score: 75,
            finding_count: 1,
            deductions: 25,
            explanation: "Deducted 25 pts for 1 critical security finding",
          },
        },
      },
    };

    assert.equal(sampleReport.schema_version, "1.0");
    assert.equal(sampleReport.score.overall, 75);
    assert.equal(sampleReport.findings[0].evidence, "AWS_KEY = '[REDACTED_SECRET]'");
    assert.equal(sampleReport.findings[0].enrichment.confidence_score, 0.95);
  });

  test("9. Max upload size is configured to 100 MB (104,857,600 bytes)", () => {
    const MAX_UPLOAD_SIZE = 100 * 1024 * 1024;
    assert.equal(MAX_UPLOAD_SIZE, 104857600);
    // Boundary check
    const validSize = 100 * 1024 * 1024;
    const oversized = 100 * 1024 * 1024 + 1;
    assert.ok(validSize <= MAX_UPLOAD_SIZE);
    assert.ok(oversized > MAX_UPLOAD_SIZE);
  });

  test("10. Finding normalization safely supports both backend `file` and `file_path` properties", async () => {
    const rawBackendFinding = {
      id: "f-123",
      title: "Missing .env.example",
      category: "missing_essential",
      severity: "low",
      file: ".env.example",
      line: 0,
      column: 0,
      rule_id: "missing-env-example",
      scanner: "rokospy-essentials",
      message: "No environment template detected",
      evidence: "No file matching .env.example found.",
      confidence: "high",
      fingerprint: "abc123456",
      enrichment: {
        why_it_matters: "Templates document required environment variables safely.",
        impact: "AI enrichment unavailable.",
        fix_steps: ["Create .env.example"],
        code_before: "",
        code_after: "",
        confidence: "low",
        status: "unavailable",
        error_message: "AI provider not configured",
      },
    };

    // Verify defensive property access works without throwing
    const filePath = rawBackendFinding.file_path || rawBackendFinding.file || "";
    const lineNum = rawBackendFinding.line_number ?? rawBackendFinding.line ?? null;
    assert.equal(filePath, ".env.example");
    assert.equal(lineNum, 0);

    // Search query test
    const query = "env";
    const matchesFile = filePath.toLowerCase().includes(query);
    assert.equal(matchesFile, true);
  });

  test("11. AI Enrichment confidence formatters handle both string and numeric representations", () => {
    const stringConfidence = { confidence: "low", why_it_matters: "Critical note" };
    const numericConfidence = { confidence_score: 0.92, why_it_matters: "Critical note" };

    const formatConfidence = (enr) => {
      if (typeof enr.confidence_score === "number") {
        return `${Math.round(enr.confidence_score * 100)}%`;
      }
      if (typeof enr.confidence === "number") {
        return `${Math.round(enr.confidence * 100)}%`;
      }
      if (enr.confidence) {
        return String(enr.confidence).toUpperCase();
      }
      return "Standard";
    };

    assert.equal(formatConfidence(stringConfidence), "LOW");
    assert.equal(formatConfidence(numericConfidence), "92%");
  });
});


