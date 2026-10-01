"""Unit tests for Phase 7.5 Project Intelligence, Structure, Architecture, and Coverage."""

import json
import tempfile
from pathlib import Path
from rokospy_analyzer.intelligence.manifest_parser import ManifestParser
from rokospy_analyzer.intelligence.structure_analyzer import StructureAnalyzer
from rokospy_analyzer.intelligence.architecture_analyzer import ArchitectureAnalyzer
from rokospy_analyzer.intelligence.coverage_calculator import CoverageCalculator
from rokospy_analyzer.scanners.intelligence_scanner import ProjectIntelligenceScanner
from rokospy_analyzer.discovery.detector import ProjectDetector
from rokospy_analyzer.pipeline import AnalyzerPipeline


def test_manifest_parser_js():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pkg_json = {
            "name": "test-app",
            "dependencies": {
                "express": "^4.18.2",
                "pg": "^8.11.0",
                "prisma": "^5.0.0",
                "jsonwebtoken": "^9.0.0",
            },
            "devDependencies": {
                "jest": "^29.0.0",
                "typescript": "^5.0.0",
            },
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg_json), encoding="utf-8")
        (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")

        result = ManifestParser.parse_workspace(tmp_path)
        assert result["has_lockfile"] is True
        assert "package-lock.json" in result["lockfile_names"]
        assert "Express" in result["frameworks"]
        assert "Jest" in result["test_frameworks"]
        assert "Prisma" in result["db_orm_detected"]
        assert "JWT" in result["auth_mechanisms_detected"]
        assert "express" in result["direct_dependencies"]


def test_structure_analyzer_fastapi_and_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        app_code = """
import os
from fastapi import FastAPI

app = FastAPI()
api_key = os.getenv("API_SECRET_KEY")
db_url = os.environ.get("DATABASE_URL")

@app.get("/users")
def get_users():
    return []

@app.post("/users/create")
def create_user(name: str):
    return {"name": name}
"""
        (tmp_path / "app.py").write_text(app_code, encoding="utf-8")
        (tmp_path / ".env.example").write_text("API_SECRET_KEY=\n", encoding="utf-8")

        intel = StructureAnalyzer.analyze_workspace(tmp_path, "test-fastapi", "local")
        assert intel.project_type == "backend_api"
        assert len(intel.routes_detected) == 2
        route_paths = [r.path for r in intel.routes_detected]
        assert "/users" in route_paths
        assert "/users/create" in route_paths
        assert "API_SECRET_KEY" in intel.env_vars_used
        assert "DATABASE_URL" in intel.env_vars_used
        assert "API_SECRET_KEY" in intel.env_vars_documented
        assert "DATABASE_URL" in intel.missing_env_vars


def test_architecture_analyzer_rules():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # 1. God Module (>500 lines)
        god_lines = ["# Line " + str(i) for i in range(550)]
        (tmp_path / "huge_module.py").write_text("\n".join(god_lines), encoding="utf-8")

        # 2. Command Injection & SQL Concat
        vuln_code = """
import os
import subprocess

def run_cmd(user_input):
    os.system(f"ping {user_input}")
    subprocess.Popen(f"ls {user_input}")

def run_query(cursor, user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
"""
        (tmp_path / "vuln.py").write_text(vuln_code, encoding="utf-8")

        # 3. Frontend layer boundary violation
        (tmp_path / "components").mkdir()
        frontend_code = """
import fs from 'fs';
import { useState } from 'react';

export default function MyComponent() {
    return <div>Hello</div>;
}
"""
        (tmp_path / "components" / "Card.tsx").write_text(frontend_code, encoding="utf-8")

        findings = ArchitectureAnalyzer.analyze_workspace(tmp_path)
        rule_ids = {f.rule_id for f in findings}
        assert "excessive-module-size" in rule_ids
        assert "insecure-command-execution" in rule_ids
        assert "raw-sql-concatenation" in rule_ids
        assert "layer-boundary-violation" in rule_ids


def test_coverage_calculator():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "README.md").write_text("# Test", encoding="utf-8")
        intel = StructureAnalyzer.analyze_workspace(tmp_path, "test", "local")
        coverage = CoverageCalculator.calculate(intel, ["rokospy-secret-scanner", "rokospy-essentials"])

        assert 50 <= coverage.overall_coverage_pct <= 100
        assert "security" in coverage.pillars
        assert "reliability" in coverage.pillars
        assert "code_quality" in coverage.pillars
        assert "performance" in coverage.pillars
        assert "architecture" in coverage.pillars
        assert "completeness" in coverage.pillars
        assert len(coverage.pillars["security"].verifiable_aspects) > 0
        assert len(coverage.pillars["security"].unverified_aspects) > 0


def test_intelligence_scanner_findings():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"lodash": "^4.0.0"}}), encoding="utf-8")
        (tmp_path / "index.js").write_text('const secret = process.env.SECRET_TOKEN;', encoding="utf-8")

        discovery = ProjectDetector.inspect(tmp_path, "test-intel", "local")
        scanner = ProjectIntelligenceScanner()
        status, findings, err = scanner.run(tmp_path, discovery)

        assert status == "success"
        rule_ids = {f.rule_id for f in findings}
        assert "missing-env-documentation" in rule_ids
        assert "missing-dependency-lockfile" in rule_ids


def test_pipeline_attaches_intelligence_and_coverage():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "README.md").write_text("# Pipeline Test", encoding="utf-8")
        (tmp_path / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
        (tmp_path / ".env.example").write_text("PORT=3000\n", encoding="utf-8")

        report = AnalyzerPipeline.analyze(str(tmp_path))
        assert report.coverage is not None
        assert report.coverage.overall_coverage_pct > 0
        assert report.intelligence is not None
        assert isinstance(report.intelligence.frameworks, list)
