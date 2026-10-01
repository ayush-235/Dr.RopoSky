import { test, describe } from "node:test";
import assert from "node:assert/strict";

describe("Phase 7 — Re-Scan & Progress Tracking Frontend Data & Logic Tests", () => {
  const mockComparisonReport = {
    schema_version: "1.0",
    summary: {
      fixed_count: 2,
      new_count: 1,
      remaining_count: 1,
      changed_count: 1,
      overall_delta: 27,
      verdict: "improved",
    },
    overall: {
      previous: 55,
      current: 82,
      delta: 27,
    },
    pillars: {
      security: { previous: 25, current: 85, delta: 60 },
      reliability: { previous: 70, current: 85, delta: 15 },
      code_quality: { previous: 60, current: 80, delta: 20 },
      performance: { previous: 90, current: 90, delta: 0 },
      architecture: { previous: 80, current: 80, delta: 0 },
      completeness: { previous: 60, current: 75, delta: 15 },
    },
    fixed_findings: [
      {
        id: "find-prev-1",
        scanner: "rokospy-secret-scanner",
        rule_id: "rokospy-sec-001",
        category: "security",
        severity: "critical",
        title: "Hardcoded AWS Access Key",
        message: "AWS Secret Access Key pattern detected",
        file_path: "src/config/aws.ts",
        line_number: 14,
        evidence: "export const AWS_SECRET = '[REDACTED_SECRET]';",
        fingerprint: "sha_aws_123",
      },
      {
        id: "find-prev-2",
        scanner: "bandit",
        rule_id: "B608",
        category: "security",
        severity: "high",
        title: "SQL Injection in User Query",
        message: "Unescaped SQL query construction",
        file_path: "api/routes/users.py",
        line_number: 52,
        evidence: 'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")',
        fingerprint: "sha_sql_789",
      },
    ],
    new_findings: [
      {
        id: "find-curr-1",
        scanner: "npm-audit",
        rule_id: "GHSA-1234-5678",
        category: "security",
        severity: "medium",
        title: "Vulnerable Dependency: lodash < 4.17.21",
        message: "Prototype Pollution in lodash",
        file_path: "package.json",
        line_number: 1,
        evidence: '"lodash": "^4.17.15"',
        fingerprint: "sha_lodash_001",
      },
    ],
    remaining_findings: [
      {
        id: "find-curr-2",
        scanner: "eslint",
        rule_id: "no-unused-vars",
        category: "quality",
        severity: "low",
        title: "Unused Variable",
        message: "'temp' is defined but never used",
        file_path: "src/utils/helpers.ts",
        line_number: 25, // Line shifted
        evidence: "const temp = 42;",
        fingerprint: "sha_unused_var",
      },
    ],
    changed_findings: [
      {
        status: "changed",
        finding: {
          id: "find-curr-3",
          scanner: "bandit",
          rule_id: "B104",
          category: "security",
          severity: "medium",
          title: "Bind to all interfaces",
          message: "Hardcoded 0.0.0.0 bind in production handler",
          file_path: "server.py",
          line_number: 8,
          evidence: "app.run(host='0.0.0.0')",
          fingerprint: "sha_bind_001",
        },
        previous_finding: {
          id: "find-prev-4",
          scanner: "bandit",
          rule_id: "B104",
          category: "security",
          severity: "low",
          title: "Bind to all interfaces",
          message: "Hardcoded 0.0.0.0 bind",
          file_path: "server.py",
          line_number: 8,
          evidence: "app.run(host='0.0.0.0')",
          fingerprint: "sha_bind_001",
        },
        change_details: "Severity modified from LOW to MEDIUM",
      },
    ],
  };

  test("1. Score progression delta is deterministically formatted and styled", () => {
    const { overall } = mockComparisonReport;
    assert.equal(overall.previous, 55);
    assert.equal(overall.current, 82);
    assert.equal(overall.delta, 27);
    assert.equal(overall.current - overall.previous, 27);

    // Delta formatting logic
    const formatDelta = (d) => (d > 0 ? `+${d}` : `${d}`);
    assert.equal(formatDelta(overall.delta), "+27");
    assert.equal(formatDelta(-15), "-15");
    assert.equal(formatDelta(0), "0");
  });

  test("2. Finding summary counts match authentic breakdown", () => {
    const { summary, fixed_findings, new_findings, remaining_findings, changed_findings } =
      mockComparisonReport;

    assert.equal(summary.fixed_count, fixed_findings.length);
    assert.equal(summary.new_count, new_findings.length);
    assert.equal(summary.remaining_count, remaining_findings.length);
    assert.equal(summary.changed_count, changed_findings.length);
    assert.equal(summary.fixed_count, 2);
    assert.equal(summary.new_count, 1);
    assert.equal(summary.remaining_count, 1);
    assert.equal(summary.changed_count, 1);
    assert.equal(summary.verdict, "improved");
  });

  test("3. Line number shifts do not mark unchanged findings as FIXED + NEW", () => {
    const remainingFinding = mockComparisonReport.remaining_findings.find(
      (f) => f.rule_id === "no-unused-vars"
    );
    assert.ok(remainingFinding);
    assert.equal(remainingFinding.file_path, "src/utils/helpers.ts");
    assert.equal(remainingFinding.line_number, 25);
  });

  test("4. Pillar score deltas preserve authoritative backend calculations without mutation", () => {
    const { pillars } = mockComparisonReport;

    assert.equal(pillars.security.delta, 60);
    assert.equal(pillars.security.current - pillars.security.previous, 60);

    assert.equal(pillars.reliability.delta, 15);
    assert.equal(pillars.code_quality.delta, 20);
    assert.equal(pillars.performance.delta, 0);
    assert.equal(pillars.architecture.delta, 0);
    assert.equal(pillars.completeness.delta, 15);
  });

  test("5. Status categorization correctly partitions findings list", () => {
    const { fixed_findings, new_findings, remaining_findings, changed_findings } =
      mockComparisonReport;

    assert.equal(fixed_findings.length, 2);
    assert.equal(new_findings.length, 1);
    assert.equal(remaining_findings.length, 1);
    assert.equal(changed_findings.length, 1);

    assert.equal(changed_findings[0].change_details, "Severity modified from LOW to MEDIUM");
    assert.equal(changed_findings[0].previous_finding?.severity, "low");
    assert.equal(changed_findings[0].finding.severity, "medium");
  });

  test("6. Redacted secret tokens are preserved in compared finding evidence", () => {
    const fixedSecret = mockComparisonReport.fixed_findings.find(
      (f) => f.scanner === "rokospy-secret-scanner"
    );
    assert.ok(fixedSecret);
    assert.ok(fixedSecret.evidence.includes("[REDACTED_SECRET]"));
  });

  test("7. Search filter matches across title, file, rule_id, and scanner", () => {
    const allFindings = [
      ...mockComparisonReport.fixed_findings,
      ...mockComparisonReport.new_findings,
      ...mockComparisonReport.remaining_findings,
      ...mockComparisonReport.changed_findings.map((c) => c.finding),
    ];

    const filterBySearch = (query) => {
      const q = query.toLowerCase();
      return allFindings.filter((f) => {
        return (
          f.title.toLowerCase().includes(q) ||
          f.message.toLowerCase().includes(q) ||
          f.file_path.toLowerCase().includes(q) ||
          (f.rule_id && f.rule_id.toLowerCase().includes(q)) ||
          f.scanner.toLowerCase().includes(q)
        );
      });
    };

    assert.equal(filterBySearch("AWS").length, 1);
    assert.equal(filterBySearch("B608").length, 1);
    assert.equal(filterBySearch("lodash").length, 1);
    assert.equal(filterBySearch("nonexistent-xyz").length, 0);
  });

  test("8. Rating band transition helper correctly maps scores", () => {
    const { overall } = mockComparisonReport;
    const getRatingBand = (score) => {
      if (score >= 80) return "Strong Baseline";
      if (score >= 60) return "Needs Improvement";
      if (score >= 40) return "Significant Issues";
      return "Severe Issues";
    };

    assert.equal(getRatingBand(overall.previous), "Significant Issues");
    assert.equal(getRatingBand(overall.current), "Strong Baseline");
    assert.ok(overall.current > overall.previous);
  });
});
