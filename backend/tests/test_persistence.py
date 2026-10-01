"""Tests for Supabase PostgreSQL persistence adapter and Re-Scan endpoints."""

import pytest
from unittest.mock import patch
from app.db.supabase_client import SupabaseStore, supabase_store
from app.services.persistence_service import (
    save_analysis_report,
    rescan_project,
    get_project_scans,
    get_scan_comparison,
    get_comparison_by_scan,
)


@pytest.fixture(autouse=True)
def clean_store():
    """Ensure clean store before and after each test."""
    supabase_store.clear_memory()
    yield
    supabase_store.clear_memory()


def test_supabase_store_project_crud():
    """Test project creation, retrieval, and deduplication by source_url."""
    store = SupabaseStore(supabase_url="", service_role_key="")

    p1 = store.get_or_create_project(
        name="test-repo",
        source_type="git",
        source_url="https://github.com/owner/test-repo",
    )
    assert p1["id"] is not None
    assert p1["name"] == "test-repo"

    # Same source_url returns existing project
    p2 = store.get_or_create_project(
        name="test-repo-updated",
        source_type="git",
        source_url="https://github.com/owner/test-repo",
    )
    assert p2["id"] == p1["id"]

    # Retrieval
    retrieved = store.get_project(p1["id"])
    assert retrieved is not None
    assert retrieved["id"] == p1["id"]


def test_supabase_store_scan_and_findings_crud():
    """Test scan creation and retrieval with findings."""
    store = SupabaseStore(supabase_url="", service_role_key="")
    project = store.get_or_create_project("my-project", "zip")

    sample_report = {
        "score": {
            "overall": 85,
            "security": 90,
            "reliability": 80,
            "code_quality": 85,
            "performance": 95,
            "architecture": 80,
            "completeness": 80,
        },
        "summary": {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 1,
            "info": 0,
        },
        "findings": [
            {
                "id": "find-1",
                "fingerprint": "fp-1",
                "title": "Hardcoded secret",
                "category": "security",
                "severity": "high",
                "file_path": "config.py",
                "line_number": 12,
                "enrichment": {
                    "why_it_matters": "Secrets in repo are dangerous",
                    "confidence_score": 0.95,
                },
            }
        ],
    }

    scan = store.create_scan(project["id"], sample_report)
    assert scan["id"] is not None
    assert scan["overall_score"] == 85
    assert scan["high_count"] == 1

    # Retrieve scan
    retrieved = store.get_scan(scan["id"])
    assert retrieved is not None
    assert retrieved["id"] == scan["id"]

    # Retrieve project scan history
    scans = store.get_project_scans(project["id"])
    assert len(scans) == 1
    assert scans[0]["id"] == scan["id"]


def test_save_analysis_report_integration():
    """Test saving an analysis report modifies report dict in place with project_id and scan_id."""
    report_dict = {
        "project": {
            "name": "api-service",
            "source_type": "git",
            "target_url": "https://github.com/org/api-service",
            "languages": ["python"],
            "manifests": ["requirements.txt"],
        },
        "analysis": {"started_at": "2026-10-01T00:00:00Z", "duration_ms": 120, "files_analyzed": 10},
        "scanners": [],
        "findings": [],
        "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
        "category_summary": {"bug": 0, "security": 0, "performance": 0, "quality": 0, "missing_essential": 0, "architecture": 0},
        "score": {
            "overall": 100,
            "rating_band": "A",
            "security": 100,
            "reliability": 100,
            "code_quality": 100,
            "performance": 100,
            "architecture": 100,
            "completeness": 100,
            "categories": {},
        },
    }

    proj, scan = save_analysis_report(
        report_data=report_dict,
        source_type="git",
        source_url="https://github.com/org/api-service",
    )

    assert "project_id" in report_dict
    assert "scan_id" in report_dict
    assert report_dict["project_id"] == proj["id"]
    assert report_dict["scan_id"] == scan["id"]


def test_rescan_project_workflow():
    """Test full rescan workflow: baseline scan -> rescan -> deterministic delta comparison."""
    # Baseline scan
    baseline_report = {
        "schema_version": "1.0",
        "project": {
            "name": "sample-repo",
            "source_type": "git",
            "target_url": "https://github.com/org/sample-repo",
            "languages": ["python"],
            "manifests": [],
        },
        "analysis": {"started_at": "2026-10-01T00:00:00Z", "duration_ms": 100, "files_analyzed": 5},
        "scanners": [],
        "findings": [
            {
                "id": "f1",
                "title": "Hardcoded Secret",
                "category": "security",
                "severity": "critical",
                "scanner": "secret-scanner",
                "rule_id": "SEC001",
                "message": "Hardcoded secret detected",
                "file": "app.py",
                "line": 10,
                "evidence": "API_KEY = 'secret123'",
                "fingerprint": "fp1",
            }
        ],
        "summary": {"critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0},
        "category_summary": {"bug": 0, "security": 1, "performance": 0, "quality": 0, "missing_essential": 0, "architecture": 0},
        "score": {
            "overall": 60,
            "rating_band": "D",
            "security": 40,
            "reliability": 80,
            "code_quality": 90,
            "performance": 100,
            "architecture": 90,
            "completeness": 90,
            "categories": {},
        },
    }

    proj, base_scan = save_analysis_report(
        report_data=baseline_report,
        source_type="git",
        source_url="https://github.com/org/sample-repo",
    )

    # Current/fixed report
    fixed_report = {
        "schema_version": "1.0",
        "project": {
            "name": "sample-repo",
            "source_type": "git",
            "target_url": "https://github.com/org/sample-repo",
            "languages": ["python"],
            "manifests": [],
        },
        "analysis": {"started_at": "2026-10-01T00:05:00Z", "duration_ms": 90, "files_analyzed": 5},
        "scanners": [],
        "findings": [],  # Secret fixed!
        "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
        "category_summary": {"bug": 0, "security": 0, "performance": 0, "quality": 0, "missing_essential": 0, "architecture": 0},
        "score": {
            "overall": 95,
            "rating_band": "A",
            "security": 100,
            "reliability": 90,
            "code_quality": 95,
            "performance": 100,
            "architecture": 95,
            "completeness": 95,
            "categories": {},
        },
    }

    with patch("app.services.persistence_service.run_analysis", return_value=fixed_report):
        result = rescan_project(proj["id"])

        assert result["previous_scan_id"] == base_scan["id"]
        assert result["current_scan_id"] != base_scan["id"]
        comp = result["comparison"]
        assert comp["summary"]["fixed_count"] == 1
        assert comp["summary"]["new_count"] == 0
        assert comp["summary"]["verdict"] == "improved"
        assert comp["overall"]["delta"] == 35
        assert comp["pillars"]["security"]["delta"] == 60


def test_api_projects_endpoints(client):
    """Test API endpoints for project scan history, rescan, and comparison."""
    # 1. Create a baseline scan
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    baseline_report = {
        "schema_version": "1.0",
        "project": {
            "name": f"api-demo-{unique_id}",
            "source_type": "git",
            "target_url": f"https://github.com/demo/api-demo-{unique_id}",
            "languages": ["javascript"],
            "manifests": ["package.json"],
        },
        "analysis": {"started_at": "2026-10-01T00:00:00Z", "duration_ms": 100, "files_analyzed": 5},
        "scanners": [],
        "findings": [],
        "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
        "category_summary": {"bug": 0, "security": 0, "performance": 0, "quality": 0, "missing_essential": 0, "architecture": 0},
        "score": {
            "overall": 90,
            "rating_band": "A",
            "security": 90,
            "reliability": 90,
            "code_quality": 90,
            "performance": 90,
            "architecture": 90,
            "completeness": 90,
            "categories": {},
        },
    }

    proj, scan = save_analysis_report(
        report_data=baseline_report,
        source_type="git",
        source_url=f"https://github.com/demo/api-demo-{unique_id}",
    )

    # Test GET /api/v1/projects/{project_id}/scans
    res = client.get(f"/api/v1/projects/{proj['id']}/scans")
    assert res.status_code == 200
    scans = res.json()
    assert len(scans) == 1
    assert scans[0]["id"] == scan["id"]

    # Test POST /api/v1/projects/{project_id}/rescan
    with patch("app.services.persistence_service.run_analysis", return_value=baseline_report):
        rescan_res = client.post(f"/api/v1/projects/{proj['id']}/rescan")
        assert rescan_res.status_code == 200
        rescan_data = rescan_res.json()
        assert "comparison" in rescan_data
        current_scan_id = rescan_data["current_scan_id"]

        # Test GET /api/v1/scans/{scan_id}/comparison
        comp_res = client.get(f"/api/v1/scans/{current_scan_id}/comparison")
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert comp_data["project_id"] == proj["id"]

    # Test 404 for unknown project
    res_404 = client.post("/api/v1/projects/non-existent-id/rescan")
    assert res_404.status_code == 404


def test_persistence_mode_activation_and_diagnostics(client):
    """Verify that credentials dictate Supabase vs Local Fallback mode and health endpoint displays safe diagnostic."""
    # 1. Without credentials -> Local Fallback
    fallback_store = SupabaseStore(supabase_url="", service_role_key="")
    assert fallback_store.is_live is False

    # 2. With valid credentials -> Supabase live
    live_store = SupabaseStore(
        supabase_url="https://xyzcompany.supabase.co",
        service_role_key="eyJh...testkey",
    )
    assert live_store.is_live is True

    # 3. Test /health endpoint diagnostic
    health_res = client.get("/api/v1/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert "persistence" in health_data
    assert health_data["persistence"] in ("Supabase", "Local Fallback")
