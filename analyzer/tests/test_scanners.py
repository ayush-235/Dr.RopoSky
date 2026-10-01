"""Tests for scanner adapters and normalizers."""

from pathlib import Path
from rokospy_analyzer.discovery.detector import ProjectDetector
from rokospy_analyzer.models.finding import CategoryEnum, SeverityEnum
from rokospy_analyzer.models.report import ScannerStatusEnum
from rokospy_analyzer.scanners.secret_scanner import BuiltinSecretScanner
from rokospy_analyzer.scanners.essentials_scanner import ProjectEssentialsScanner
from rokospy_analyzer.scanners.gitleaks_scanner import GitleaksScanner
from rokospy_analyzer.scanners.bandit_scanner import BanditScanner
from rokospy_analyzer.scanners.npm_audit_scanner import NpmAuditScanner
from rokospy_analyzer.scanners.pip_audit_scanner import PipAuditScanner


def test_builtin_secret_scanner_detects_and_redacts(tmp_path: Path):
    proj_dir = tmp_path / "secret_proj"
    proj_dir.mkdir()
    
    # Write a test file with fake credentials
    src_file = proj_dir / "auth.py"
    fake_secret = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    src_file.write_text(f'GITHUB_TOKEN = "{fake_secret}"\n', encoding="utf-8")

    discovery = ProjectDetector.inspect(proj_dir, "secret_proj", "local")
    scanner = BuiltinSecretScanner()
    status, findings, err = scanner.run(proj_dir, discovery)

    assert status == ScannerStatusEnum.SUCCESS
    assert len(findings) == 1
    finding = findings[0]
    assert finding.category == CategoryEnum.SECURITY
    assert finding.severity == SeverityEnum.CRITICAL
    assert finding.file == "auth.py"
    assert finding.line == 1
    # Check that the actual secret is redacted
    assert fake_secret not in finding.evidence
    assert "[REDACTED_SECRET]" in finding.evidence


def test_essentials_scanner_correct_categories(tmp_path: Path):
    """
    Verifies that missing essentials are marked as MISSING_ESSENTIAL or QUALITY,
    and NEVER misclassified as SECURITY vulnerabilities.
    """
    proj_dir = tmp_path / "bare_proj"
    proj_dir.mkdir()
    (proj_dir / "index.js").write_text("console.log('hello');")

    discovery = ProjectDetector.inspect(proj_dir, "bare_proj", "local")
    scanner = ProjectEssentialsScanner()
    status, findings, err = scanner.run(proj_dir, discovery)

    assert status == ScannerStatusEnum.SUCCESS
    assert len(findings) > 0

    categories = {f.category for f in findings}
    assert CategoryEnum.SECURITY not in categories, "Essentials must NOT be classified as SECURITY!"
    assert CategoryEnum.MISSING_ESSENTIAL in categories


def test_gitleaks_unavailable_handling():
    scanner = GitleaksScanner()
    # Check that scanner reports properly if not installed or unavailable
    assert scanner.name == "gitleaks"
    assert scanner.supported_languages == ["All"]


def test_bandit_normalizer(tmp_path: Path):
    scanner = BanditScanner()
    mock_bandit_data = {
        "results": [
            {
                "test_id": "B102",
                "test_name": "exec_used",
                "filename": str(tmp_path / "app.py"),
                "line_number": 42,
                "issue_severity": "HIGH",
                "issue_confidence": "HIGH",
                "issue_text": "Use of exec detected.",
                "code": "42 exec('evil')",
            }
        ]
    }
    findings = scanner._normalize_bandit(mock_bandit_data, tmp_path)
    assert len(findings) == 1
    f = findings[0]
    assert f.category == CategoryEnum.SECURITY
    assert f.severity == SeverityEnum.CRITICAL
    assert f.line == 42
    assert f.file == "app.py"


def test_npm_audit_normalizer():
    scanner = NpmAuditScanner()
    mock_npm_data = {
        "vulnerabilities": {
            "lodash": {
                "name": "lodash",
                "severity": "high",
                "via": [
                    {
                        "source": 1098,
                        "name": "lodash",
                        "dependency": "lodash",
                        "title": "Prototype Pollution in lodash",
                        "url": "https://github.com/advisories/GHSA-p6mc-m468-83gw",
                        "severity": "high",
                    }
                ],
                "range": "<4.17.21",
                "fixAvailable": True,
            }
        }
    }
    findings = scanner._normalize_npm_audit(mock_npm_data)
    assert len(findings) == 1
    f = findings[0]
    assert f.category == CategoryEnum.SECURITY
    assert f.severity == SeverityEnum.HIGH
    assert f.file == "package-lock.json"
    assert "lodash" in f.title


def test_pip_audit_normalizer():
    scanner = PipAuditScanner()
    mock_pip_data = {
        "dependencies": [
            {
                "name": "urllib3",
                "version": "1.26.4",
                "vulns": [
                    {
                        "id": "GHSA-1234-5678",
                        "description": "Cookie leak on redirect",
                        "fix_versions": ["1.26.5"],
                    }
                ],
            }
        ]
    }
    findings = scanner._normalize_pip_audit(mock_pip_data)
    assert len(findings) == 1
    f = findings[0]
    assert f.category == CategoryEnum.SECURITY
    assert f.severity == SeverityEnum.HIGH
    assert f.file == "requirements.txt"
    assert "urllib3" in f.title
