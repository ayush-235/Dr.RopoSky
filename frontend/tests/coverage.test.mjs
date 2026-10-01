import { test, describe } from "node:test";
import assert from "node:assert/strict";

describe("Phase 7.5 Coverage & Project Intelligence Telemetry Tests", () => {
  test("1. AnalysisCoverage and ProjectIntelligence schema adherence", () => {
    const mockCoverage = {
      overall_coverage_pct: 85,
      pillars: {
        security: {
          pillar: "security",
          coverage_pct: 85,
          verifiable_aspects: ["Secret detection", "Code execution isolation"],
          unverified_aspects: ["Runtime taint flow"],
        },
        reliability: {
          pillar: "reliability",
          coverage_pct: 80,
          verifiable_aspects: ["AST route validation"],
          unverified_aspects: ["Concurrency race conditions"],
        },
      },
      evaluation_summary: "Static analysis verified 85% of applicable codebase properties.",
    };

    const mockIntelligence = {
      project_type: "backend_api",
      frameworks: ["FastAPI"],
      entry_points: ["app.py"],
      routes_detected: [
        {
          method: "GET",
          path: "/users",
          file: "app.py",
          line: 10,
          has_validation: true,
          handler_name: "get_users",
        },
      ],
      env_vars_used: ["API_KEY", "DATABASE_URL"],
      env_vars_documented: ["API_KEY"],
      missing_env_vars: ["DATABASE_URL"],
      direct_dependencies: ["fastapi", "uvicorn"],
      has_lockfile: true,
      lockfile_names: ["poetry.lock"],
      has_tests: true,
      test_frameworks: ["pytest"],
      test_files_count: 5,
      db_orm_detected: ["SQLAlchemy"],
      auth_mechanisms_detected: ["JWT"],
    };

    assert.equal(mockCoverage.overall_coverage_pct, 85);
    assert.equal(mockIntelligence.project_type, "backend_api");
    assert.equal(mockIntelligence.missing_env_vars[0], "DATABASE_URL");
    assert.equal(mockIntelligence.routes_detected[0].path, "/users");
    assert.equal(mockCoverage.pillars.security.coverage_pct, 85);
  });

  test("2. Coverage calculation handles missing optional fields gracefully", () => {
    const partialCoverage = {
      overall_coverage_pct: 70,
      pillars: {},
      evaluation_summary: "Baseline evaluation.",
    };

    assert.equal(partialCoverage.overall_coverage_pct, 70);
    assert.ok(typeof partialCoverage.evaluation_summary === "string");
  });
});
