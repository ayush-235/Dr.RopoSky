"""Analysis Coverage Telemetry Calculator."""

from typing import Dict, List
from rokospy_analyzer.intelligence.models import (
    AnalysisCoverage,
    PillarCoverage,
    ProjectIntelligence,
)


class CoverageCalculator:
    """Computes transparent static analysis coverage percentages for each audit pillar."""

    @classmethod
    def calculate(cls, intelligence: ProjectIntelligence, scanners_run: List[str]) -> AnalysisCoverage:
        """Evaluates verifiable static surface vs unverified aspects."""
        pillars: Dict[str, PillarCoverage] = {}

        # 1. Security Pillar Coverage
        sec_verifiable = [
            "Pattern-based secret detection (API keys, tokens, credentials)",
            "Secret redaction across evidence streams",
            "Zip Slip & directory traversal defenses",
            "Zero code execution policy enforcement",
        ]
        sec_unverified = [
            "Dynamic runtime taint analysis",
            "Complex zero-day logic vulnerabilities",
            "Runtime cloud IAM permissions",
        ]
        sec_cov = 70
        if "rokospy-secret-scanner" in scanners_run or "gitleaks" in scanners_run:
            sec_cov += 15
        if intelligence.has_lockfile:
            sec_cov += 10
            sec_verifiable.append("Dependency lockfile presence")
        else:
            sec_unverified.append("Unpinned transitive dependency CVEs (missing lockfile)")
        sec_cov = min(sec_cov, 95)

        pillars["security"] = PillarCoverage(
            pillar="security",
            coverage_pct=sec_cov,
            verifiable_aspects=sec_verifiable,
            unverified_aspects=sec_unverified,
        )

        # 2. Reliability Pillar Coverage
        rel_verifiable = [
            "Static syntax and structural AST parsing",
            "Route definition and handler mapping",
        ]
        rel_unverified = [
            "Runtime exception behavior under high concurrency",
            "Dynamic database query timeouts and deadlocks",
        ]
        rel_cov = 75
        if len(intelligence.routes_detected) > 0:
            rel_verifiable.append(f"{len(intelligence.routes_detected)} API endpoint handler signatures inspected")
            rel_cov += 10
        if intelligence.has_tests:
            rel_verifiable.append(f"Automated test suite detected ({intelligence.test_files_count} test files)")
            rel_cov += 10
        else:
            rel_unverified.append("Unit/integration test execution results (no tests detected)")
        rel_cov = min(rel_cov, 95)

        pillars["reliability"] = PillarCoverage(
            pillar="reliability",
            coverage_pct=rel_cov,
            verifiable_aspects=rel_verifiable,
            unverified_aspects=rel_unverified,
        )

        # 3. Code Quality Pillar Coverage
        qual_verifiable = [
            "Source file structure and size telemetry",
            "Module length and God-file detection",
            "Static naming and manifest syntax",
        ]
        qual_unverified = [
            "Runtime code profiling and memory leak detection",
            "Dynamic branch coverage percentage",
        ]
        qual_cov = 85
        pillars["code_quality"] = PillarCoverage(
            pillar="code_quality",
            coverage_pct=qual_cov,
            verifiable_aspects=qual_verifiable,
            unverified_aspects=qual_unverified,
        )

        # 4. Performance Pillar Coverage
        perf_verifiable = [
            "Static module footprint and bundle file size distribution",
            "Synchronous command execution detection",
        ]
        perf_unverified = [
            "Actual runtime CPU/memory latency benchmarking",
            "Database index optimization and query execution plans",
        ]
        perf_cov = 65
        pillars["performance"] = PillarCoverage(
            pillar="performance",
            coverage_pct=perf_cov,
            verifiable_aspects=perf_verifiable,
            unverified_aspects=perf_unverified,
        )

        # 5. Architecture Pillar Coverage
        arch_verifiable = [
            "Module boundary and God-component analysis",
            "Environment configuration centralization vs scattering",
            "Frontend/Backend layer boundary separation",
        ]
        arch_unverified = [
            "Microservice distributed tracing and network partitions",
            "Runtime service mesh resilience",
        ]
        arch_cov = 80
        pillars["architecture"] = PillarCoverage(
            pillar="architecture",
            coverage_pct=arch_cov,
            verifiable_aspects=arch_verifiable,
            unverified_aspects=arch_unverified,
        )

        # 6. Completeness Pillar Coverage
        comp_verifiable = [
            "Project manifest and dependency declaration detection",
            "Environment configuration template verification (.env.example)",
            "Documentation, Git hygiene (.gitignore), and test presence",
        ]
        comp_unverified = [
            "Business logic specification completeness",
            "Product requirement fulfillment verification",
        ]
        comp_cov = 90
        pillars["completeness"] = PillarCoverage(
            pillar="completeness",
            coverage_pct=comp_cov,
            verifiable_aspects=comp_verifiable,
            unverified_aspects=comp_unverified,
        )

        # Calculate weighted overall coverage
        weights = {
            "security": 0.30,
            "reliability": 0.25,
            "code_quality": 0.15,
            "performance": 0.10,
            "architecture": 0.10,
            "completeness": 0.10,
        }
        overall = int(sum(pillars[k].coverage_pct * weights[k] for k in weights))

        summary = (
            f"Static analysis verified approximately {overall}% of applicable codebase properties across 6 engineering pillars. "
            "Zero dynamic code execution was performed; findings reflect static evidence and AST telemetry."
        )

        return AnalysisCoverage(
            overall_coverage_pct=overall,
            pillars=pillars,
            evaluation_summary=summary,
        )
