"""Unit and integration tests for Phase 7.6 Security Detection & Authorization Intelligence."""

import json
import tempfile
from pathlib import Path
from rokospy_analyzer.intelligence.structure_analyzer import StructureAnalyzer
from rokospy_analyzer.intelligence.security_analyzer import SecurityAnalyzer
from rokospy_analyzer.scanners.intelligence_scanner import ProjectIntelligenceScanner
from rokospy_analyzer.discovery.detector import ProjectDetector
from rokospy_analyzer.pipeline import AnalyzerPipeline


def test_predictable_secret_defaults_and_safe_counterexample():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Insecure file with predictable default secret
        insecure_code = '''
import os
JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_key_123")
API_SECRET = os.environ.get("API_SECRET", "hardcoded_api_key_456")
SAFE_VAR = os.getenv("APP_ENV", "development")
'''
        (tmp_path / "config.py").write_text(insecure_code, encoding="utf-8")

        # Safe file with environment-only secrets
        safe_code = '''
import os
SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
'''
        (tmp_path / "safe_config.py").write_text(safe_code, encoding="utf-8")

        intel = StructureAnalyzer.analyze_workspace(tmp_path, "test-secrets", "local")
        findings = SecurityAnalyzer.analyze_workspace(tmp_path, intel)

        rule_ids = [f.rule_id for f in findings]
        assert "predictable-secret-default" in rule_ids
        
        # Verify safe file did not generate false positives
        safe_findings = [f for f in findings if f.file == "safe_config.py"]
        assert len(safe_findings) == 0


def test_hardcoded_secret_assignments():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        code = '''
SECRET_KEY = "my_super_secret_production_key"
PLACEHOLDER_KEY = ""
EXAMPLE_SECRET = "your-secret-here"
'''
        (tmp_path / "secrets.py").write_text(code, encoding="utf-8")
        intel = StructureAnalyzer.analyze_workspace(tmp_path, "test", "local")
        findings = SecurityAnalyzer.analyze_workspace(tmp_path, intel)

        rule_ids = [f.rule_id for f in findings]
        assert "hardcoded-secret-assignment" in rule_ids
        # Ensure placeholder keys are not flagged
        secret_findings = [f for f in findings if f.rule_id == "hardcoded-secret-assignment"]
        assert len(secret_findings) == 1
        assert "SECRET_KEY" in secret_findings[0].title


def test_debug_and_demo_mode_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        code = '''
import os
DEBUG = True
DEMO_MODE = os.getenv("DEMO_MODE", "true")
DEMO_AUTH = True
'''
        (tmp_path / "settings.py").write_text(code, encoding="utf-8")
        intel = StructureAnalyzer.analyze_workspace(tmp_path, "test", "local")
        findings = SecurityAnalyzer.analyze_workspace(tmp_path, intel)

        rule_ids = {f.rule_id for f in findings}
        assert "debug-mode-default-enabled" in rule_ids
        assert "demo-mode-default-enabled" in rule_ids


def test_static_otp_and_auth_bypass():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        auth_code = '''
def verify_otp(entered_otp):
    if entered_otp == "123456":
        return True
    return False
'''
        (tmp_path / "auth.py").write_text(auth_code, encoding="utf-8")

        # Test fixture in tests directory should be ignored
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_auth.py").write_text('mock_otp = "123456"', encoding="utf-8")

        intel = StructureAnalyzer.analyze_workspace(tmp_path, "test", "local")
        findings = SecurityAnalyzer.analyze_workspace(tmp_path, intel)

        rule_ids = {f.rule_id for f in findings}
        assert "static-otp-bypass" in rule_ids
        # Ensure tests/ directory was not flagged
        test_dir_findings = [f for f in findings if "tests/" in f.file]
        assert len(test_dir_findings) == 0


def test_payment_bypass_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        code = '''
def verify_payment(order_id, signature, demo=False):
    if demo:
        return True
    return check_signature(order_id, signature)
'''
        (tmp_path / "payment_service.py").write_text(code, encoding="utf-8")
        intel = StructureAnalyzer.analyze_workspace(tmp_path, "test", "local")
        findings = SecurityAnalyzer.analyze_workspace(tmp_path, intel)

        rule_ids = {f.rule_id for f in findings}
        assert "payment-verification-bypass" in rule_ids


def test_route_authentication_and_authorization_analysis():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        app_code = '''
from fastapi import FastAPI, Depends

app = FastAPI()

def get_current_user():
    return {"id": 1}

def require_admin(user = Depends(get_current_user)):
    return user

# 1. Unprotected admin endpoint -> MUST be flagged
@app.post("/admin/system/reset")
def reset_system():
    return {"status": "reset"}

# 2. Protected admin endpoint -> SAFE
@app.get("/admin/dashboard", dependencies=[Depends(require_admin)])
def admin_dashboard():
    return {"metrics": []}

# 3. Unprotected sensitive payment route -> MUST be flagged
@app.post("/payments/refund")
def refund_payment(order_id: str):
    return {"refunded": True}

# 4. Protected sensitive route -> SAFE
@app.post("/payments/create")
def create_payment(user = Depends(get_current_user)):
    return {"created": True}
'''
        (tmp_path / "main.py").write_text(app_code, encoding="utf-8")
        intel = StructureAnalyzer.analyze_workspace(tmp_path, "test", "local")
        findings = SecurityAnalyzer.analyze_workspace(tmp_path, intel)

        rule_ids = [f.rule_id for f in findings]
        assert "unprotected-admin-endpoint" in rule_ids
        assert "missing-endpoint-authentication" in rule_ids

        admin_findings = [f for f in findings if f.rule_id == "unprotected-admin-endpoint"]
        assert len(admin_findings) == 1
        assert "/admin/system/reset" in admin_findings[0].evidence


def test_permissive_cors_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        code = '''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''
        (tmp_path / "server.py").write_text(code, encoding="utf-8")
        intel = StructureAnalyzer.analyze_workspace(tmp_path, "test", "local")
        findings = SecurityAnalyzer.analyze_workspace(tmp_path, intel)

        rule_ids = {f.rule_id for f in findings}
        assert "permissive-cors-wildcard" in rule_ids


def test_insecure_session_and_file_upload():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        code = '''
import os
from flask import Flask, request

app = Flask(__name__)
app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = False

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    file.save(os.path.join("/tmp/uploads", file.filename))
    return "OK"
'''
        (tmp_path / "app.py").write_text(code, encoding="utf-8")
        intel = StructureAnalyzer.analyze_workspace(tmp_path, "test", "local")
        findings = SecurityAnalyzer.analyze_workspace(tmp_path, intel)

        rule_ids = {f.rule_id for f in findings}
        assert "insecure-session-configuration" in rule_ids
        assert "insecure-file-upload" in rule_ids


def test_full_pipeline_vulnerable_benchmark_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Benchmark-style project structure with multiple real vulnerabilities
        (tmp_path / "README.md").write_text("# Benchmark App\n", encoding="utf-8")
        (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
        (tmp_path / ".env.example").write_text("PORT=8000\n", encoding="utf-8")
        
        app_code = '''
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

DEBUG = True
DEMO_MODE = True
SECRET_KEY = os.getenv("SECRET_KEY", "predictable-dev-secret-key-12345")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/auth/verify-otp")
def verify_otp(code: str):
    if code == "123456":
        return {"token": "demo-token", "role": "admin"}
    return {"error": "invalid"}

@app.post("/admin/reset-database")
def reset_db():
    return {"status": "cleared"}

@app.post("/payments/verify")
def verify_payment(order_id: str, demo: bool = False):
    if demo:
        return {"verified": True}
    return {"verified": False}
'''
        (tmp_path / "app.py").write_text(app_code, encoding="utf-8")

        report = AnalyzerPipeline.analyze(str(tmp_path))
        
        # Verify findings were triggered
        rule_ids = {f.rule_id for f in report.findings}
        assert "predictable-secret-default" in rule_ids
        assert "debug-mode-default-enabled" in rule_ids
        assert "demo-mode-default-enabled" in rule_ids
        assert "static-otp-bypass" in rule_ids
        assert "unprotected-admin-endpoint" in rule_ids
        assert "payment-verification-bypass" in rule_ids
        assert "permissive-cors-wildcard" in rule_ids

        # Deterministic score reflects security issues
        assert report.score is not None
        assert report.score.security < 100
        assert report.score.overall < 100
        assert report.summary.high >= 5
