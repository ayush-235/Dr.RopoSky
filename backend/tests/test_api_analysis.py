"""Tests for POST /api/v1/analyze endpoint."""

import io
import zipfile
from unittest.mock import patch
from fastapi.testclient import TestClient


def create_sample_zip(files: dict[str, str]) -> io.BytesIO:
    """Helper to create an in-memory ZIP file."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    buf.seek(0)
    return buf


def test_analyze_empty_request_rejected(client: TestClient):
    """Providing neither github_url nor zip_file returns 400."""
    response = client.post("/api/v1/analyze", data={})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_SOURCE"


def test_analyze_both_sources_rejected(client: TestClient):
    """Providing both github_url and zip_file returns 400."""
    zip_buf = create_sample_zip({"README.md": "# Test"})
    response = client.post(
        "/api/v1/analyze",
        data={"github_url": "https://github.com/owner/repo"},
        files={"zip_file": ("test.zip", zip_buf, "application/zip")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_SOURCE"


def test_analyze_valid_zip_upload(client: TestClient):
    """Valid ZIP upload performs complete analysis and returns AnalysisReport structure."""
    zip_buf = create_sample_zip({
        "README.md": "# Project Title",
        ".gitignore": "node_modules/\n*.pyc\n",
        "LICENSE": "MIT License",
        ".env.example": "PORT=8000\n",
        "app.py": "def main():\n    pass\n",
    })

    response = client.post(
        "/api/v1/analyze",
        files={"zip_file": ("clean_project.zip", zip_buf, "application/zip")},
    )
    assert response.status_code == 200
    report = response.json()

    # Verify AnalysisReport structure
    assert report["schema_version"] == "1.0"
    assert "project" in report
    assert "analysis" in report
    assert "scanners" in report
    assert "findings" in report
    assert "summary" in report
    assert "category_summary" in report
    assert "score" in report

    # Verify Score components
    score = report["score"]
    assert "overall" in score
    assert "rating_band" in score
    assert "security" in score
    assert "reliability" in score
    assert "code_quality" in score
    assert "performance" in score
    assert "architecture" in score
    assert "completeness" in score
    assert "categories" in score
    assert len(score["categories"]) == 6


def test_analyze_invalid_file_extension(client: TestClient):
    """Uploading non-zip file returns 400 INVALID_FILE_TYPE."""
    buf = io.BytesIO(b"not a zip")
    response = client.post(
        "/api/v1/analyze",
        files={"zip_file": ("malicious.tar.gz", buf, "application/gzip")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_FILE_TYPE"


def test_analyze_valid_github_url_mocked(client: TestClient):
    """Valid GitHub URL passes validation and executes pipeline."""
    with patch("app.services.analysis_service.AnalyzerPipeline.analyze") as mock_analyze:
        from rokospy_analyzer.models.report import (
            AnalysisReport,
            ProjectMetadata,
            AnalysisExecutionInfo,
            SeveritySummary,
            CategorySummary,
        )
        from rokospy_analyzer.scoring.models import ProjectScore, CategoryScore

        mock_analyze.return_value = AnalysisReport(
            schema_version="1.0",
            project=ProjectMetadata(
                name="repo",
                source_type="git",
                languages=["Python"],
                manifests=[],
            ),
            analysis=AnalysisExecutionInfo(duration_ms=100, files_analyzed=5),
            scanners=[],
            findings=[],
            summary=SeveritySummary(),
            category_summary=CategorySummary(),
            score=ProjectScore(
                overall=100,
                rating_band="Strong Baseline",
                security=100,
                reliability=100,
                code_quality=100,
                performance=100,
                architecture=100,
                completeness=100,
                categories={
                    "security": CategoryScore(category="security", score=100),
                    "reliability": CategoryScore(category="reliability", score=100),
                    "code_quality": CategoryScore(category="code_quality", score=100),
                    "performance": CategoryScore(category="performance", score=100),
                    "architecture": CategoryScore(category="architecture", score=100),
                    "completeness": CategoryScore(category="completeness", score=100),
                },
            ),
        )

        response = client.post(
            "/api/v1/analyze",
            data={"github_url": "https://github.com/owner/sample-repo"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schema_version"] == "1.0"
        assert data["score"]["overall"] == 100
        mock_analyze.assert_called_once()


def test_analyze_gemini_failure_does_not_break_analysis(client: TestClient):
    """When Gemini provider fails or is not available, static analysis and deterministic score succeed."""
    zip_buf = create_sample_zip({
        "README.md": "# Title",
        ".gitignore": ".env\n",
        "app.py": "x = 1\n",
    })

    with patch("app.services.analysis_service._create_ai_provider", return_value=None):
        response = client.post(
            "/api/v1/analyze",
            files={"zip_file": ("test.zip", zip_buf, "application/zip")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] is not None
        assert "overall" in data["score"]


def test_analyze_github_acquisition_failure_handled(client: TestClient):
    """When git clone fails (e.g. non-existent repo), returns 500 ANALYSIS_FAILED with clean message."""
    response = client.post(
        "/api/v1/analyze",
        data={"github_url": "https://github.com/nonexistent-org-1234908123/nonexistent-repo-123098"},
    )
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "ANALYSIS_FAILED"
    # Never leak internal stack trace
    assert "Traceback" not in str(data)

