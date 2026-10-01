"""Tests for repository and workspace acquisition."""

import io
import zipfile
from pathlib import Path
import pytest
from rokospy_analyzer.acquisition.workspace import ManagedWorkspace
from rokospy_analyzer.acquisition.zip_extractor import SafeZipExtractor


def test_safe_zip_extraction(tmp_path: Path):
    zip_path = tmp_path / "valid.zip"
    dest_dir = tmp_path / "out"

    # Create safe zip
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("src/main.py", "print('hello')\n")
        zf.writestr("README.md", "# Test Project\n")

    extracted = SafeZipExtractor.extract(zip_path, dest_dir)
    assert (extracted / "src" / "main.py").exists()
    assert (extracted / "README.md").exists()
    assert (extracted / "src" / "main.py").read_text() == "print('hello')\n"


def test_managed_workspace_local_dir(tmp_path: Path):
    src_dir = tmp_path / "my_project"
    src_dir.mkdir()
    (src_dir / "index.js").write_text("console.log('test');")

    with ManagedWorkspace(str(src_dir)) as (ws_path, source_type, proj_name):
        assert ws_path.exists()
        assert (ws_path / "index.js").exists()
        assert source_type == "local"
        assert proj_name == "my_project"

    # Workspace directory must be cleaned up
    assert not ws_path.exists()


def test_safe_git_cloner_invalid_scheme(tmp_path: Path):
    """SafeGitCloner rejects unsupported or dangerous URL schemes."""
    from rokospy_analyzer.acquisition.git_cloner import SafeGitCloner, AcquisitionError
    with pytest.raises(AcquisitionError, match="Invalid or unsupported"):
        SafeGitCloner.clone("file:///etc/passwd", tmp_path / "out")


def test_safe_git_cloner_acquisition_failure_handled(tmp_path: Path):
    """Git clone failures produce a clean AcquisitionError."""
    from rokospy_analyzer.acquisition.git_cloner import SafeGitCloner, AcquisitionError
    with pytest.raises(AcquisitionError, match="Failed to clone repository"):
        SafeGitCloner.clone("https://github.com/nonexistent-org-0982348712398/nonexistent-repo-987234", tmp_path / "out")


def test_managed_workspace_github_url_cleanup(tmp_path: Path):
    """ManagedWorkspace with GitHub URL clones safely and cleans up temporary workspace."""
    from unittest.mock import patch
    from rokospy_analyzer.acquisition.git_cloner import SafeGitCloner

    def mock_clone(repo_url, destination_dir):
        destination_dir.mkdir(parents=True, exist_ok=True)
        (destination_dir / "README.md").write_text("# Mocked Repo")
        (destination_dir / "main.py").write_text("print('hello')")
        return destination_dir

    with patch.object(SafeGitCloner, "clone", side_effect=mock_clone):
        with ManagedWorkspace("https://github.com/example/sample-app") as (ws_path, source_type, proj_name):
            assert ws_path.exists()
            assert (ws_path / "README.md").exists()
            assert source_type == "github"
            assert proj_name == "sample-app"

        # Ephemeral workspace must be completely removed upon exit
        assert not ws_path.exists()

