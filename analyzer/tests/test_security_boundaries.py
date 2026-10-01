"""Security boundary tests for Rokospy Analyzer.

Verifies:
1. Untrusted application code is NEVER executed during analysis.
2. Zip Slip path traversal attacks are strictly rejected.
3. Resource quotas (file count and extracted size) are enforced.
"""

import io
import os
import zipfile
from pathlib import Path
import pytest
from rokospy_analyzer.acquisition.zip_extractor import SafeZipExtractor, ExtractionError
from rokospy_analyzer.pipeline import AnalyzerPipeline


def test_zero_untrusted_code_execution(tmp_path: Path):
    """
    Creates a malicious repository with active payload code in top-level files
    designed to write a marker file if executed.
    Asserts that the marker file is NEVER created during inspection and analysis.
    """
    repo_dir = tmp_path / "untrusted_repo"
    repo_dir.mkdir()

    marker_file = tmp_path / "MALICIOUS_EXECUTION_MARKER.txt"
    assert not marker_file.exists()

    # Create Python malicious payload
    py_payload = repo_dir / "app.py"
    py_payload.write_text(
        f"""
import os
# If this file is imported or executed, it will create a marker file
with open(r"{marker_file}", "w") as f:
    f.write("EXECUTED!")
print("HOST COMPROMISED")
""",
        encoding="utf-8",
    )

    # Create Node.js malicious payload
    js_payload = repo_dir / "index.js"
    js_payload.write_text(
        f"""
const fs = require('fs');
fs.writeFileSync("{str(marker_file).replace('\\', '/')}", "NODE EXECUTED");
""",
        encoding="utf-8",
    )

    # Create package.json with malicious scripts
    pkg_json = repo_dir / "package.json"
    pkg_json.write_text(
        """{
  "name": "malicious-repo",
  "scripts": {
    "postinstall": "touch MALICIOUS_MARKER.txt",
    "start": "node index.js"
  }
}""",
        encoding="utf-8",
    )

    # Run the complete analyzer pipeline
    report = AnalyzerPipeline.analyze(str(repo_dir))

    # Assert that the marker file was NEVER created
    assert not marker_file.exists(), "CRITICAL SECURITY BREACH: Untrusted code was executed!"
    assert report.project.name == "untrusted_repo"
    assert "Python" in report.project.languages
    assert "JavaScript" in report.project.languages


def test_zip_slip_path_traversal_rejection(tmp_path: Path):
    """
    Creates a malicious ZIP archive with Zip Slip directory traversal payloads (../../evil.py).
    Asserts that SafeZipExtractor rejects the archive and raises ExtractionError.
    """
    malicious_zip = tmp_path / "zip_slip.zip"
    dest_dir = tmp_path / "extracted"

    # Construct in-memory malicious zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add normal file
        zf.writestr("normal.txt", "safe content")
        # Add traversal entry
        zf.writestr("../../escaped_payload.txt", "MALICIOUS PAYLOAD OUTSIDE DESTINATION")

    malicious_zip.write_bytes(zip_buffer.getvalue())

    with pytest.raises(ExtractionError, match="Path traversal"):
        SafeZipExtractor.extract(malicious_zip, dest_dir)

    # Verify escaped payload was never written to parent directory
    escaped_file = tmp_path / "escaped_payload.txt"
    assert not escaped_file.exists(), "CRITICAL SECURITY BREACH: Zip Slip file escaped destination!"


def test_zip_absolute_path_rejection(tmp_path: Path):
    """
    Creates a malicious ZIP archive with absolute path payloads (/evil.txt or C:\\evil.txt).
    Asserts that SafeZipExtractor rejects the archive.
    """
    malicious_zip = tmp_path / "absolute_path.zip"
    dest_dir = tmp_path / "extracted"

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("/root/evil.txt", "absolute path content")

    malicious_zip.write_bytes(zip_buffer.getvalue())

    with pytest.raises(ExtractionError, match="Absolute path in archive rejected"):
        SafeZipExtractor.extract(malicious_zip, dest_dir)


def test_zip_file_count_quota_enforcement(tmp_path: Path, monkeypatch):
    """
    Enforces maximum file count limit on extracted archives.
    """
    from rokospy_analyzer.config import config
    monkeypatch.setattr(config, "MAX_FILE_COUNT", 5)

    oversized_zip = tmp_path / "too_many_files.zip"
    dest_dir = tmp_path / "extracted"

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i in range(10):
            zf.writestr(f"file_{i}.txt", f"content {i}")

    oversized_zip.write_bytes(zip_buffer.getvalue())

    with pytest.raises(ExtractionError, match="Archive exceeds maximum file count limit"):
        SafeZipExtractor.extract(oversized_zip, dest_dir)


def test_zip_uncompressed_size_quota_enforcement(tmp_path: Path, monkeypatch):
    """
    Enforces maximum uncompressed extracted size quota on extracted archives.
    """
    from rokospy_analyzer.config import config
    # Set to a small limit for testing (e.g. 1 KB)
    monkeypatch.setattr(config, "MAX_EXTRACTED_SIZE_MB", 0.001)

    oversized_zip = tmp_path / "too_large_uncompressed.zip"
    dest_dir = tmp_path / "extracted"

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write 2 KB into zip
        zf.writestr("large_file.txt", "A" * 2048)

    oversized_zip.write_bytes(zip_buffer.getvalue())

    with pytest.raises(ExtractionError, match="Archive uncompressed size exceeds limit"):
        SafeZipExtractor.extract(oversized_zip, dest_dir)


def test_default_safety_limits_constants():
    """
    Verifies default safety constants are set to the updated project limits (100 MB repo, 300 MB extracted, 3000 files).
    """
    from rokospy_analyzer.config import config
    assert config.MAX_REPO_SIZE_MB == 100
    assert config.MAX_EXTRACTED_SIZE_MB == 300
    assert config.MAX_FILE_COUNT == 3000
