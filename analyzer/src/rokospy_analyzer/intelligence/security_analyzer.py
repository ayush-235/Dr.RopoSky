"""Static Security, Authentication, Authorization, and Configuration Analyzer."""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from rokospy_analyzer.filtering.file_filter import FileFilter
from rokospy_analyzer.intelligence.models import RouteInfo, ProjectIntelligence
from rokospy_analyzer.models.finding import (
    CategoryEnum,
    SeverityEnum,
    ConfidenceEnum,
    NormalizedFinding,
)
from rokospy_analyzer.normalization.fingerprint import FindingFingerprint


class SecurityAnalyzer:
    """Performs static security analysis covering auth, credentials, debug, CORS, sessions, and payments."""

    SECRET_ENV_KEYS = {
        "SECRET_KEY",
        "JWT_SECRET",
        "API_SECRET",
        "PRIVATE_KEY",
        "ENCRYPTION_KEY",
        "AUTH_SECRET",
        "TOKEN_SECRET",
        "SESSION_SECRET",
        "SIGNING_KEY",
        "DATABASE_PASSWORD",
        "DB_PASSWORD",
        "APP_SECRET",
    }

    # Regex patterns for environment fallback credentials
    PY_ENV_DEFAULT_REGEX = re.compile(
        r"(?:os\.getenv|os\.environ\.get)\s*\(\s*['\"]([A-Z0-9_]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)"
    )
    JS_ENV_DEFAULT_REGEX = re.compile(
        r"(?:process\.env\.([A-Z0-9_]+)|process\.env\[['\"]([A-Z0-9_]+)['\"]\])\s*(?:\|\||\?\?)\s*['\"]([^'\"]+)['\"]"
    )

    # Hardcoded assignment regex (e.g. SECRET_KEY = "mysecret123")
    HARDCODED_SECRET_ASSIGN_REGEX = re.compile(
        r"^(?:[A-Z0-9_]*_)?(SECRET_KEY|JWT_SECRET|API_SECRET|PRIVATE_KEY|AUTH_SECRET|TOKEN_SECRET|SESSION_SECRET)\s*=\s*['\"]([^'\"]{4,})['\"]",
        re.MULTILINE,
    )

    # Debug mode regex
    DEBUG_MODE_REGEX = re.compile(
        r"(?:DEBUG|FLASK_DEBUG)\s*=\s*(?:True|1|['\"]true['\"]|['\"]1['\"]|os\.getenv\(['\"](?:DEBUG|FLASK_DEBUG)['\"]\s*,\s*['\"](?:true|1|True)['\"]\))",
        re.IGNORECASE,
    )

    # Demo/Test mode regex
    DEMO_MODE_REGEX = re.compile(
        r"(DEMO_MODE|DEMO_AUTH|DEMO_PAYMENT_MODE|TEST_MODE|MOCK_AUTH|MOCK_PAYMENT)\s*=\s*(?:True|1|['\"]true['\"]|['\"]1['\"]|os\.getenv\(['\"][^'\"]*['\"]\s*,\s*['\"](?:true|1|True)['\"]\))",
        re.IGNORECASE,
    )

    # Static OTP regex
    STATIC_OTP_REGEX = re.compile(
        r"(?:OTP|DEFAULT_OTP|DEMO_OTP|STATIC_OTP)\s*==?\s*['\"]([0-9]{4,6})['\"]|if\s+(?:otp|entered_otp|code)\s+(?:==\s*['\"]([0-9]{4,6})['\"]|in\s*\[\s*['\"][0-9]+['\"])",
        re.IGNORECASE,
    )

    # CORS Wildcard regex
    CORS_WILDCARD_REGEX = re.compile(
        r"(?:allow_origins\s*=\s*\[\s*['\"]\*(?:['\"])?\s*\]|allow_origins\s*=\s*['\"]\*(?:['\"])?|Access-Control-Allow-Origin['\"]\s*,\s*['\"]\*(?:['\"])?|cors\(\s*\{\s*origin\s*:\s*['\"]\*(?:['\"])?\s*\}\s*\)|CORS\s*\(\s*app\s*\))",
        re.IGNORECASE,
    )

    # Insecure Session Cookie regex
    INSECURE_SESSION_REGEX = re.compile(
        r"(?:SESSION_COOKIE_SECURE|SESSION_COOKIE_HTTPONLY|secure|httpOnly)[\"']?\s*\]?\s*=\s*(?:False|false|0)",
        re.IGNORECASE,
    )


    @classmethod
    def is_test_file(cls, rel_path: str) -> bool:
        """Determines if a file is an isolated test fixture or unit test."""
        lower = rel_path.lower()
        parts = lower.split("/")
        return any(
            p in {"tests", "test", "__tests__", "fixtures", "mocks", "spec"} for p in parts
        ) or lower.startswith("test_") or lower.endswith("_test.py") or ".test." in lower or ".spec." in lower

    @classmethod
    def analyze_workspace(cls, workspace_path: Path, intelligence: ProjectIntelligence) -> List[NormalizedFinding]:
        """Runs full suite of general static security and authorization detectors."""
        findings: List[NormalizedFinding] = []
        analyzable_files = FileFilter.collect_analyzable_files(workspace_path)

        for file_path in analyzable_files:
            rel_path = str(file_path.relative_to(workspace_path)).replace("\\", "/")
            if cls.is_test_file(rel_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            lines = content.splitlines()
            ext = file_path.suffix.lower()

            # 1. Detect Predictable Default Secrets in os.getenv / process.env
            cls._check_predictable_secret_defaults(lines, rel_path, findings)

            # 2. Detect Hardcoded Secret Assignments
            cls._check_hardcoded_secret_assignments(lines, rel_path, findings)

            # 3. Detect Debug Mode Enabled by Default
            cls._check_debug_mode_defaults(lines, rel_path, findings)

            # 4. Detect Demo/Test Mode Enabled by Default
            cls._check_demo_mode_defaults(lines, rel_path, findings)

            # 5. Detect Static OTP / Auth Bypass
            cls._check_static_otp_bypass(lines, rel_path, findings)

            # 6. Detect Payment Bypass
            cls._check_payment_bypass(lines, rel_path, findings)

            # 7. Detect Permissive CORS
            cls._check_permissive_cors(lines, rel_path, findings)

            # 8. Detect Insecure Session / Cookie Configuration
            cls._check_insecure_sessions(lines, rel_path, findings)

            # 9. Detect Insecure File Upload Handling
            cls._check_insecure_file_upload(lines, rel_path, findings)

            # 10. Detect Insecure Fallback Identity
            cls._check_insecure_fallback_identities(lines, rel_path, findings)

        # 11. Endpoint Authentication & Authorization Analysis using Route Discovery
        cls._check_route_security(intelligence, findings)

        return findings

    @classmethod
    def _check_predictable_secret_defaults(
        cls, lines: List[str], rel_path: str, findings: List[NormalizedFinding]
    ) -> None:
        for line_idx, line in enumerate(lines, start=1):
            py_match = cls.PY_ENV_DEFAULT_REGEX.search(line)
            if py_match:
                var_name = py_match.group(1)
                default_val = py_match.group(2).strip()
                if var_name in cls.SECRET_ENV_KEYS and default_val and default_val.lower() not in {"none", "", "false"}:
                    fp = FindingFingerprint.generate("rokospy-security", "predictable-secret-default", rel_path, line_idx)
                    findings.append(
                        NormalizedFinding(
                            id=fp,
                            title=f"Predictable Default Secret Fallback ({var_name})",
                            category=CategoryEnum.SECURITY,
                            severity=SeverityEnum.HIGH,
                            file=rel_path,
                            file_path=rel_path,
                            line=line_idx,
                            line_number=line_idx,
                            column=0,
                            column_number=0,
                            rule_id="predictable-secret-default",
                            scanner="rokospy-security-intelligence",
                            message=(
                                f"Security-sensitive variable `{var_name}` configures a predictable fallback default value ('{default_val}'). "
                                "If the environment variable is not supplied in production, the application operates with known, insecure credentials."
                            ),
                            evidence=line.strip(),
                            confidence=ConfidenceEnum.HIGH,
                            source="rokospy-security-intelligence",
                            fingerprint=fp,
                        )
                    )

            js_match = cls.JS_ENV_DEFAULT_REGEX.search(line)
            if js_match:
                var_name = js_match.group(1) or js_match.group(2)
                default_val = js_match.group(3).strip()
                if var_name in cls.SECRET_ENV_KEYS and default_val and default_val.lower() not in {"none", "", "false"}:
                    fp = FindingFingerprint.generate("rokospy-security", "predictable-secret-default", rel_path, line_idx)
                    findings.append(
                        NormalizedFinding(
                            id=fp,
                            title=f"Predictable Default Secret Fallback ({var_name})",
                            category=CategoryEnum.SECURITY,
                            severity=SeverityEnum.HIGH,
                            file=rel_path,
                            file_path=rel_path,
                            line=line_idx,
                            line_number=line_idx,
                            column=0,
                            column_number=0,
                            rule_id="predictable-secret-default",
                            scanner="rokospy-security-intelligence",
                            message=(
                                f"Security-sensitive variable `{var_name}` specifies a fallback default string ('{default_val}'). "
                                "If unconfigured in deployment, the service will run with predictable secret material."
                            ),
                            evidence=line.strip(),
                            confidence=ConfidenceEnum.HIGH,
                            source="rokospy-security-intelligence",
                            fingerprint=fp,
                        )
                    )

    @classmethod
    def _check_hardcoded_secret_assignments(
        cls, lines: List[str], rel_path: str, findings: List[NormalizedFinding]
    ) -> None:
        for line_idx, line in enumerate(lines, start=1):
            # Skip comments and imports
            trimmed = line.strip()
            if trimmed.startswith("#") or trimmed.startswith("//") or "import " in trimmed or "from " in trimmed:
                continue
            match = cls.HARDCODED_SECRET_ASSIGN_REGEX.search(line)
            if match:
                var_name = match.group(1)
                val = match.group(2)
                # Ignore placeholders
                if val.lower() in {"your-secret-here", "changeme", "example", "placeholder", "test", ""}:
                    continue
                # If not inside os.getenv / process.env
                if "os.getenv" not in line and "process.env" not in line:
                    fp = FindingFingerprint.generate("rokospy-security", "hardcoded-secret-assignment", rel_path, line_idx)
                    findings.append(
                        NormalizedFinding(
                            id=fp,
                            title=f"Hardcoded Security Secret Assignment ({var_name})",
                            category=CategoryEnum.SECURITY,
                            severity=SeverityEnum.HIGH,
                            file=rel_path,
                            file_path=rel_path,
                            line=line_idx,
                            line_number=line_idx,
                            column=0,
                            column_number=0,
                            rule_id="hardcoded-secret-assignment",
                            scanner="rokospy-security-intelligence",
                            message=(
                                f"Security secret `{var_name}` is directly assigned a hardcoded literal value in source code. "
                                "Hardcoded secrets can be extracted from source repositories and allow unauthorized token signing or decryption."
                            ),
                            evidence=line.strip(),
                            confidence=ConfidenceEnum.HIGH,
                            source="rokospy-security-intelligence",
                            fingerprint=fp,
                        )
                    )

    @classmethod
    def _check_debug_mode_defaults(
        cls, lines: List[str], rel_path: str, findings: List[NormalizedFinding]
    ) -> None:
        for line_idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if trimmed.startswith("#") or trimmed.startswith("//"):
                continue
            if cls.DEBUG_MODE_REGEX.search(line):
                fp = FindingFingerprint.generate("rokospy-security", "debug-mode-default-enabled", rel_path, line_idx)
                findings.append(
                    NormalizedFinding(
                        id=fp,
                        title="Debug/Development Mode Enabled by Default",
                        category=CategoryEnum.SECURITY,
                        severity=SeverityEnum.HIGH,
                        file=rel_path,
                        file_path=rel_path,
                        line=line_idx,
                        line_number=line_idx,
                        column=0,
                        column_number=0,
                        rule_id="debug-mode-default-enabled",
                        scanner="rokospy-security-intelligence",
                        message=(
                            "Debug/development mode is enabled by default and may expose diagnostic stack traces, "
                            "interactive debugging interfaces, or unsafe development behaviors in production."
                        ),
                        evidence=line.strip(),
                        confidence=ConfidenceEnum.HIGH,
                        source="rokospy-security-intelligence",
                        fingerprint=fp,
                    )
                )

    @classmethod
    def _check_demo_mode_defaults(
        cls, lines: List[str], rel_path: str, findings: List[NormalizedFinding]
    ) -> None:
        for line_idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if trimmed.startswith("#") or trimmed.startswith("//"):
                continue
            match = cls.DEMO_MODE_REGEX.search(line)
            if match:
                flag_name = match.group(1)
                fp = FindingFingerprint.generate("rokospy-security", "demo-mode-default-enabled", rel_path, line_idx)
                findings.append(
                    NormalizedFinding(
                        id=fp,
                        title=f"Security-Sensitive Demo/Test Mode Enabled ({flag_name})",
                        category=CategoryEnum.SECURITY,
                        severity=SeverityEnum.HIGH,
                        file=rel_path,
                        file_path=rel_path,
                        line=line_idx,
                        line_number=line_idx,
                        column=0,
                        column_number=0,
                        rule_id="demo-mode-default-enabled",
                        scanner="rokospy-security-intelligence",
                        message=(
                            f"Demo/test flag `{flag_name}` is enabled by default. In production environments, demo modes can "
                            "bypass authentication checks, simulate payments without fund transfer, or expose unauthenticated privileged actions."
                        ),
                        evidence=line.strip(),
                        confidence=ConfidenceEnum.HIGH,
                        source="rokospy-security-intelligence",
                        fingerprint=fp,
                    )
                )

    @classmethod
    def _check_static_otp_bypass(
        cls, lines: List[str], rel_path: str, findings: List[NormalizedFinding]
    ) -> None:
        for line_idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if trimmed.startswith("#") or trimmed.startswith("//"):
                continue
            match = cls.STATIC_OTP_REGEX.search(line)
            if match:
                fp = FindingFingerprint.generate("rokospy-security", "static-otp-bypass", rel_path, line_idx)
                findings.append(
                    NormalizedFinding(
                        id=fp,
                        title="Static OTP / Authentication Bypass Pattern",
                        category=CategoryEnum.SECURITY,
                        severity=SeverityEnum.HIGH,
                        file=rel_path,
                        file_path=rel_path,
                        line=line_idx,
                        line_number=line_idx,
                        column=0,
                        column_number=0,
                        rule_id="static-otp-bypass",
                        scanner="rokospy-security-intelligence",
                        message=(
                            "Hardcoded verification token or static OTP comparison detected in authentication logic. "
                            "Attackers can bypass multi-factor authentication using the hardcoded default token."
                        ),
                        evidence=line.strip(),
                        confidence=ConfidenceEnum.HIGH,
                        source="rokospy-security-intelligence",
                        fingerprint=fp,
                    )
                )

    @classmethod
    def _check_payment_bypass(
        cls, lines: List[str], rel_path: str, findings: List[NormalizedFinding]
    ) -> None:
        full_text = "\n".join(lines).lower()
        if "payment" in rel_path.lower() or "order" in rel_path.lower() or "checkout" in rel_path.lower() or "verify" in rel_path.lower() or "verify" in full_text:
            for line_idx, line in enumerate(lines, start=1):
                trimmed = line.strip().lower()
                is_demo_branch = (
                    "if demo" in trimmed or "if is_test" in trimmed or "if mock" in trimmed or "if test" in trimmed or "if demo_mode" in trimmed
                )
                if is_demo_branch:
                    # Check next few lines for unconditional return
                    has_bypass_return = "return" in trimmed
                    for next_idx in range(line_idx, min(line_idx + 3, len(lines))):
                        next_line = lines[next_idx].strip().lower()
                        if "return true" in next_line or "return {'verified': true}" in next_line or 'return {"verified": true}' in next_line or "return 1" in next_line or "return true" in next_line:
                            has_bypass_return = True
                            break

                    if has_bypass_return:
                        fp = FindingFingerprint.generate("rokospy-security", "payment-verification-bypass", rel_path, line_idx)
                        findings.append(
                            NormalizedFinding(
                                id=fp,
                                title="Payment Verification / Signature Bypass Detected",
                                category=CategoryEnum.SECURITY,
                                severity=SeverityEnum.HIGH,
                                file=rel_path,
                                file_path=rel_path,
                                line=line_idx,
                                line_number=line_idx,
                                column=0,
                                column_number=0,
                                rule_id="payment-verification-bypass",
                                scanner="rokospy-security-intelligence",
                                message=(
                                    "Payment verification routine contains an unconditional success or demo bypass branch. "
                                    "Malicious actors can forge successful payment status callbacks without completing payment."
                                ),
                                evidence=line.strip(),
                                confidence=ConfidenceEnum.HIGH,
                                source="rokospy-security-intelligence",
                                fingerprint=fp,
                            )
                        )


    @classmethod
    def _check_permissive_cors(
        cls, lines: List[str], rel_path: str, findings: List[NormalizedFinding]
    ) -> None:
        for line_idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if trimmed.startswith("#") or trimmed.startswith("//"):
                continue
            if cls.CORS_WILDCARD_REGEX.search(line):
                fp = FindingFingerprint.generate("rokospy-security", "permissive-cors-wildcard", rel_path, line_idx)
                findings.append(
                    NormalizedFinding(
                        id=fp,
                        title="Permissive CORS Configuration (Wildcard Origin)",
                        category=CategoryEnum.SECURITY,
                        severity=SeverityEnum.MEDIUM,
                        file=rel_path,
                        file_path=rel_path,
                        line=line_idx,
                        line_number=line_idx,
                        column=0,
                        column_number=0,
                        rule_id="permissive-cors-wildcard",
                        scanner="rokospy-security-intelligence",
                        message=(
                            "Permissive CORS configuration detected with wildcard origin ('*'). "
                            "This permits untrusted external websites to issue cross-origin requests against the API."
                        ),
                        evidence=line.strip(),
                        confidence=ConfidenceEnum.HIGH,
                        source="rokospy-security-intelligence",
                        fingerprint=fp,
                    )
                )

    @classmethod
    def _check_insecure_sessions(
        cls, lines: List[str], rel_path: str, findings: List[NormalizedFinding]
    ) -> None:
        for line_idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if trimmed.startswith("#") or trimmed.startswith("//"):
                continue
            if cls.INSECURE_SESSION_REGEX.search(line):
                fp = FindingFingerprint.generate("rokospy-security", "insecure-session-configuration", rel_path, line_idx)
                findings.append(
                    NormalizedFinding(
                        id=fp,
                        title="Insecure Session / Cookie Security Configuration",
                        category=CategoryEnum.SECURITY,
                        severity=SeverityEnum.MEDIUM,
                        file=rel_path,
                        file_path=rel_path,
                        line=line_idx,
                        line_number=line_idx,
                        column=0,
                        column_number=0,
                        rule_id="insecure-session-configuration",
                        scanner="rokospy-security-intelligence",
                        message=(
                            "Session cookies are configured with Secure or HttpOnly disabled. "
                            "Cookies lacking these attributes can be intercepted over unencrypted HTTP or accessed by client-side scripts."
                        ),
                        evidence=line.strip(),
                        confidence=ConfidenceEnum.HIGH,
                        source="rokospy-security-intelligence",
                        fingerprint=fp,
                    )
                )

    @classmethod
    def _check_insecure_file_upload(
        cls, lines: List[str], rel_path: str, findings: List[NormalizedFinding]
    ) -> None:
        full_text = "\n".join(lines)
        if "upload" in rel_path.lower() or "file" in rel_path.lower() or "upload" in full_text.lower() or "request.files" in full_text:

            for line_idx, line in enumerate(lines, start=1):
                # Check for direct file saving without secure_filename or path traversal check
                if "file.save(" in line or ".save(os.path.join" in line or "writeFileSync(" in line:
                    if "secure_filename" not in full_text and "path.basename" not in full_text and "sanitize" not in full_text:
                        fp = FindingFingerprint.generate("rokospy-security", "insecure-file-upload", rel_path, line_idx)
                        findings.append(
                            NormalizedFinding(
                                id=fp,
                                title="Insecure File Upload: Unsanitized Destination Path",
                                category=CategoryEnum.SECURITY,
                                severity=SeverityEnum.HIGH,
                                file=rel_path,
                                file_path=rel_path,
                                line=line_idx,
                                line_number=line_idx,
                                column=0,
                                column_number=0,
                                rule_id="insecure-file-upload",
                                scanner="rokospy-security-intelligence",
                                message=(
                                    "Uploaded file is saved to filesystem without sanitizing the user-supplied filename (`secure_filename`). "
                                    "Attackers can supply path traversal filenames (`../../evil.sh`) to overwrite critical system files."
                                ),
                                evidence=line.strip(),
                                confidence=ConfidenceEnum.HIGH,
                                source="rokospy-security-intelligence",
                                fingerprint=fp,
                            )
                        )

    @classmethod
    def _check_insecure_fallback_identities(
        cls, lines: List[str], rel_path: str, findings: List[NormalizedFinding]
    ) -> None:
        for line_idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if trimmed.startswith("#") or trimmed.startswith("//"):
                continue
            if (
                ('user = {"' in line or "user = {'" in line or "currentUser = {" in line)
                and ("admin" in line.lower() or "role" in line.lower() or "id" in line.lower())
                and ("mock" in line.lower() or "fallback" in line.lower() or "default" in line.lower() or "demo" in line.lower())
            ):
                fp = FindingFingerprint.generate("rokospy-security", "insecure-fallback-identity", rel_path, line_idx)
                findings.append(
                    NormalizedFinding(
                        id=fp,
                        title="Insecure Hardcoded Fallback User Identity",
                        category=CategoryEnum.SECURITY,
                        severity=SeverityEnum.HIGH,
                        file=rel_path,
                        file_path=rel_path,
                        line=line_idx,
                        line_number=line_idx,
                        column=0,
                        column_number=0,
                        rule_id="insecure-fallback-identity",
                        scanner="rokospy-security-intelligence",
                        message=(
                            "Authentication logic provides a hardcoded fallback user object with default/elevated permissions. "
                            "Failed or unauthenticated requests may be inadvertently treated as authorized users."
                        ),
                        evidence=line.strip(),
                        confidence=ConfidenceEnum.HIGH,
                        source="rokospy-security-intelligence",
                        fingerprint=fp,
                    )
                )

    @classmethod
    def _check_route_security(
        cls, intelligence: ProjectIntelligence, findings: List[NormalizedFinding]
    ) -> None:
        """Inspects all discovered routes for missing authentication & authorization boundaries."""
        for route in intelligence.routes_detected:
            if cls.is_test_file(route.file):
                continue

            path_lower = route.path.lower()

            # 1. Admin route without auth or role check
            if route.is_admin and not route.has_auth and not route.has_role_check and not intelligence.has_global_auth:
                fp = FindingFingerprint.generate("rokospy-security", "unprotected-admin-endpoint", route.file, route.line, route.path)
                findings.append(
                    NormalizedFinding(
                        id=fp,
                        title=f"Unprotected Administrative Route ({route.method} {route.path})",
                        category=CategoryEnum.SECURITY,
                        severity=SeverityEnum.HIGH,
                        file=route.file,
                        file_path=route.file,
                        line=route.line,
                        line_number=route.line,
                        column=0,
                        column_number=0,
                        rule_id="unprotected-admin-endpoint",
                        scanner="rokospy-security-intelligence",
                        message=(
                            f"Privileged administrative endpoint `{route.method} {route.path}` does not enforce authentication "
                            "or role-based access control decorators/dependencies. Anyone with network access can execute administrative functions."
                        ),
                        evidence=f"Route: {route.method} {route.path} in {route.file}:{route.line}",
                        confidence=ConfidenceEnum.HIGH,
                        source="rokospy-security-intelligence",
                        fingerprint=fp,
                    )
                )

            # 2. Sensitive route (payment, account mutation, profile update) without auth
            elif route.is_sensitive and not route.is_admin and not route.has_auth and not intelligence.has_global_auth:
                # Exclude public auth endpoints like /login, /register, /auth/token
                if not any(auth_ep in path_lower for auth_ep in ["/login", "/signin", "/register", "/signup", "/token", "/auth/callback"]):
                    fp = FindingFingerprint.generate("rokospy-security", "missing-endpoint-authentication", route.file, route.line, route.path)
                    findings.append(
                        NormalizedFinding(
                            id=fp,
                            title=f"Missing Authentication on Sensitive Endpoint ({route.method} {route.path})",
                            category=CategoryEnum.SECURITY,
                            severity=SeverityEnum.HIGH,
                            file=route.file,
                            file_path=route.file,
                            line=route.line,
                            line_number=route.line,
                            column=0,
                            column_number=0,
                            rule_id="missing-endpoint-authentication",
                            scanner="rokospy-security-intelligence",
                            message=(
                                f"Sensitive endpoint `{route.method} {route.path}` performs critical business operations or data mutation "
                                "without requiring user authentication or credential validation."
                            ),
                            evidence=f"Route: {route.method} {route.path} in {route.file}:{route.line}",
                            confidence=ConfidenceEnum.HIGH,
                            source="rokospy-security-intelligence",
                            fingerprint=fp,
                        )
                    )

            # 3. Ownership / BOLA verification check on user-specific resource
            if (
                any(param in path_lower for param in ["{user_id}", "{id}", ":user_id", ":id", "<user_id>", "<id>"])
                and ("user" in path_lower or "profile" in path_lower or "order" in path_lower or "account" in path_lower)
                and route.has_auth
                and not route.has_ownership_check
                and not route.has_role_check
            ):
                fp = FindingFingerprint.generate("rokospy-security", "missing-ownership-verification", route.file, route.line, route.path)
                findings.append(
                    NormalizedFinding(
                        id=fp,
                        title=f"Potential Broken Object Level Authorization: {route.method} {route.path}",
                        category=CategoryEnum.SECURITY,
                        severity=SeverityEnum.MEDIUM,
                        file=route.file,
                        file_path=route.file,
                        line=route.line,
                        line_number=route.line,
                        column=0,
                        column_number=0,
                        rule_id="missing-ownership-verification",
                        scanner="rokospy-security-intelligence",
                        message=(
                            f"Endpoint `{route.method} {route.path}` references user-scoped entity identifiers without detectable "
                            "resource ownership checks (`user.id == resource.user_id`). Authenticated users may access other tenants' data."
                        ),
                        evidence=f"Route: {route.method} {route.path} in {route.file}:{route.line}",
                        confidence=ConfidenceEnum.MEDIUM,
                        source="rokospy-security-intelligence",
                        fingerprint=fp,
                    )
                )
