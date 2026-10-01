"""End-to-end integration test: API -> Workspace -> Scanners -> Redactor -> Deduplicator -> Scoring -> Report."""

import io
import zipfile
from fastapi.testclient import TestClient


def test_full_pipeline_e2e_via_fastapi(client: TestClient):
    """Verify full end-to-end scan via FastAPI with a multi-file project containing realistic findings."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Essentials
        zf.writestr("README.md", "# Realistic Test Project\n\nA full project for testing.")
        zf.writestr(".gitignore", ".env\n__pycache__/\n*.pyc\nnode_modules/\n")
        zf.writestr("LICENSE", "MIT License\nCopyright (c) 2026")
        zf.writestr(".env.example", "PORT=8000\nAPI_KEY=your_key_here\n")
        # Python file with hardcoded AWS key
        zf.writestr("app/config.py", "AWS_ACCESS_KEY = 'AKIA1111111111111111'\n")
        # Python file with clean code
        zf.writestr("app/main.py", "def add(a: int, b: int) -> int:\n    return a + b\n")

    buf.seek(0)

    response = client.post(
        "/api/v1/analyze",
        files={"zip_file": ("e2e_project.zip", buf, "application/zip")},
    )

    assert response.status_code == 200
    report = response.json()

    # 1. Report Metadata
    assert report["schema_version"] == "1.0"
    assert report["project"]["languages"] == ["Python"]
    assert report["analysis"]["files_analyzed"] >= 5

    # 2. Scanner execution results
    scanners = report["scanners"]
    assert len(scanners) > 0
    scanner_names = [s["scanner"] for s in scanners]
    assert "rokospy-secret-scanner" in scanner_names
    assert "rokospy-essentials" in scanner_names

    # 3. Secret Redaction in Findings
    findings = report["findings"]
    assert len(findings) > 0
    secret_findings = [f for f in findings if f["category"] == "security"]
    assert len(secret_findings) >= 1

    # Secret is redacted in evidence
    for f in findings:
        assert "AKIA1111111111111111" not in f.get("evidence", "")
        assert "AKIA1111111111111111" not in f.get("title", "")
        assert "AKIA1111111111111111" not in f.get("message", "")

    # 4. Deterministic Scoring
    score = report["score"]
    assert score is not None
    assert 0 <= score["overall"] <= 100
    assert "rating_band" in score
    assert "categories" in score
    categories = score["categories"]
    assert "security" in categories
    assert "completeness" in categories
    # Since all essentials (README, .gitignore, LICENSE, .env.example) exist, completeness is 100
    assert categories["completeness"]["score"] == 100
    # Since an AWS key was found, security score must be penalized
    assert categories["security"]["score"] < 100
