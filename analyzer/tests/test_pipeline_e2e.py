"""End-to-end integration tests for Rokospy AnalyzerPipeline."""

from pathlib import Path
from rokospy_analyzer.models.finding import CategoryEnum, SeverityEnum
from rokospy_analyzer.models.report import AnalysisReport
from rokospy_analyzer.pipeline import AnalyzerPipeline


def test_pipeline_clean_project(tmp_path: Path):
    clean_proj = tmp_path / "clean_project"
    clean_proj.mkdir()
    (clean_proj / "README.md").write_text("# Clean Project\nDocumentation here.\n")
    (clean_proj / ".gitignore").write_text("node_modules/\n.venv/\n")
    (clean_proj / ".env.example").write_text("API_KEY=YOUR_KEY\n")
    (clean_proj / "LICENSE").write_text("MIT License\n")
    (clean_proj / "tests").mkdir()
    (clean_proj / "tests" / "test_main.py").write_text("def test_ok(): pass\n")
    (clean_proj / "main.py").write_text("def add(a: int, b: int) -> int:\n    return a + b\n")

    report = AnalyzerPipeline.analyze(str(clean_proj))

    assert isinstance(report, AnalysisReport)
    assert report.project.name == "clean_project"
    assert "Python" in report.project.languages
    assert report.summary.critical == 0
    assert report.summary.high == 0


def test_pipeline_vulnerable_project(tmp_path: Path):
    vuln_proj = tmp_path / "vuln_project"
    vuln_proj.mkdir()
    # Add hardcoded secret
    fake_token = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
    (vuln_proj / "config.py").write_text(f'GITHUB_API_TOKEN = "{fake_token}"\n')

    report = AnalyzerPipeline.analyze(str(vuln_proj))

    assert isinstance(report, AnalysisReport)
    assert report.summary.critical >= 1
    assert report.category_summary.security >= 1

    # Ensure secret is redacted in output
    for f in report.findings:
        assert fake_token not in f.evidence
        assert fake_token not in f.message
        assert fake_token not in f.title
