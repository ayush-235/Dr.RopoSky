"""Security boundary tests for FastAPI backend."""

import io
import os
import zipfile
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient


def test_cors_headers_present(client: TestClient):
    """CORS middleware returns proper headers for allowed origins."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_github_url_rejection_schemes(client: TestClient):
    """Reject non-HTTPS schemes: file://, http://, ftp://, ssh://."""
    bad_urls = [
        "file:///etc/passwd",
        "http://github.com/owner/repo",
        "ftp://github.com/owner/repo",
        "ssh://git@github.com/owner/repo",
    ]
    for url in bad_urls:
        res = client.post("/api/v1/analyze", data={"github_url": url})
        assert res.status_code == 400
        data = res.json()
        assert data["error"]["code"] == "INVALID_URL"


def test_github_url_rejection_internal_and_private_ips(client: TestClient):
    """Reject localhost, 127.0.0.1, internal IPs, AWS metadata."""
    bad_urls = [
        "https://localhost/owner/repo",
        "https://127.0.0.1/owner/repo",
        "https://169.254.169.254/latest/meta-data",
        "https://192.168.1.1/owner/repo",
        "https://10.0.0.1/owner/repo",
        "https://gitlab.com/owner/repo",
        "https://evil-site.com/owner/repo",
    ]
    for url in bad_urls:
        res = client.post("/api/v1/analyze", data={"github_url": url})
        assert res.status_code == 400
        data = res.json()
        assert data["error"]["code"] == "INVALID_URL"


def test_github_url_rejection_embedded_credentials_and_ports(client: TestClient):
    """Reject credentials and non-standard ports."""
    bad_urls = [
        "https://user:pass@github.com/owner/repo",
        "https://github.com",
        "https://github.com/",
        "C:\\Users\\Administrator\\secret.txt",
        "/etc/shadow",
    ]
    for url in bad_urls:
        res = client.post("/api/v1/analyze", data={"github_url": url})
        assert res.status_code == 400
        data = res.json()
        assert data["error"]["code"] == "INVALID_URL"


def test_oversized_zip_upload_rejected(client: TestClient):
    """Uploads exceeding MAX_UPLOAD_SIZE_MB return 413 FILE_TOO_LARGE."""
    from app.config import backend_config
    original_limit = backend_config.MAX_UPLOAD_SIZE_MB
    backend_config.MAX_UPLOAD_SIZE_MB = 1
    try:
        large_content = b"0" * (1024 * 1024 + 1024)
        buf = io.BytesIO(large_content)
        res = client.post(
            "/api/v1/analyze",
            files={"zip_file": ("large.zip", buf, "application/zip")},
        )
        assert res.status_code == 413
        data = res.json()
        assert data["error"]["code"] == "FILE_TOO_LARGE"
    finally:
        backend_config.MAX_UPLOAD_SIZE_MB = original_limit


def test_default_backend_upload_limit_constant():
    """Default MAX_UPLOAD_SIZE_MB must be 100 MB."""
    from app.config import backend_config
    assert backend_config.MAX_UPLOAD_SIZE_MB == 100



def test_zip_slip_rejection_through_api(client: TestClient):
    """Zip slip path traversal payload in uploaded ZIP is rejected safely."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../../evil.py", "import os; os.system('calc')")
    buf.seek(0)

    res = client.post(
        "/api/v1/analyze",
        files={"zip_file": ("zip_slip.zip", buf, "application/zip")},
    )
    assert res.status_code in (400, 500)
    data = res.json()
    assert "error" in data


def test_zip_absolute_path_rejection_through_api(client: TestClient):
    """Absolute path member in uploaded ZIP is rejected safely."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("/etc/passwd", "root:x:0:0")
    buf.seek(0)

    res = client.post(
        "/api/v1/analyze",
        files={"zip_file": ("absolute_path.zip", buf, "application/zip")},
    )
    assert res.status_code in (400, 500)
    data = res.json()
    assert "error" in data


def test_zero_code_execution_through_api(client: TestClient):
    """Uploaded code with malicious setup.py or package.json must not execute."""
    buf = io.BytesIO()
    marker_content = "EXECUTION_TEST_FLAG"
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("setup.py", "import sys; print('ACTIVE_PAYLOAD')")
        zf.writestr("package.json", '{"scripts": {"postinstall": "exit 1"}}')
        zf.writestr("main.py", f"SECRET_KEY = 'AKIAIOSFODNN7EXAMPLE'\n# {marker_content}")
    buf.seek(0)

    res = client.post(
        "/api/v1/analyze",
        files={"zip_file": ("test_payload.zip", buf, "application/zip")},
    )
    assert res.status_code == 200
    report = res.json()
    findings_str = str(report["findings"])
    assert "AKIAIOSFODNN7EXAMPLE" not in findings_str
    assert "[REDACTED_SECRET]" in findings_str


def test_sanitized_500_error_no_stack_trace_or_paths(client: TestClient):
    """Internal server errors must be sanitized without exposing stack traces or filesystem paths."""
    with patch("app.services.analysis_service.AnalyzerPipeline.analyze", side_effect=Exception("Secret internal DB crash C:\\Secrets\\db.key")):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("README.md", "# Sample")
        buf.seek(0)

        res = client.post(
            "/api/v1/analyze",
            files={"zip_file": ("test.zip", buf, "application/zip")},
        )
        assert res.status_code == 500
        data = res.json()
        assert "error" in data
        assert data["error"]["code"] == "ANALYSIS_FAILED"
        # Must not leak internal paths or raw sensitive exception strings
        assert "C:\\Secrets" not in str(data)
        assert "Traceback" not in str(data)


def test_temporary_file_cleanup(client: TestClient):
    """Temporary zip files created during analysis must be unlinked."""
    import tempfile as std_tempfile
    created_tmp_paths = []

    original_named_temp = std_tempfile.NamedTemporaryFile

    def tracking_tempfile(*args, **kwargs):
        tf = original_named_temp(*args, **kwargs)
        created_tmp_paths.append(tf.name)
        return tf

    with patch("tempfile.NamedTemporaryFile", side_effect=tracking_tempfile):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("README.md", "# Test")
        buf.seek(0)

        res = client.post(
            "/api/v1/analyze",
            files={"zip_file": ("test.zip", buf, "application/zip")},
        )
        assert res.status_code == 200

    # Ensure all created temp files were cleaned up
    assert len(created_tmp_paths) > 0
    for path_str in created_tmp_paths:
        assert not os.path.exists(path_str)

