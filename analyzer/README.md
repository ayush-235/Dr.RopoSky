# Dr.RopoSky Core Static Analysis Engine (`analyzer/`)

The `analyzer/` package provides the standalone, zero-code-execution static and security analysis engine for Dr.RopoSky.

---

## 1. Scanner Suite

1. **`rokospy-secret-scanner` & `gitleaks`**: Multi-pattern entropy and regex secret detection with automatic token redaction.
2. **`rokospy-essentials`**: Repository hygiene and completeness validation (README, .gitignore, .env.example, LICENSE, test suites).
3. **`rokospy-project-intelligence`**:
   - Manifest parsing: framework detection, dependency extraction, lockfile auditing.
   - Code structure analysis: API route extraction (FastAPI AST, Express, Next.js), cross-file environment variable auditing.
   - Architectural vulnerability analysis: God modules (>500 LOC), scattered configuration, layer boundary violations.
   - Security & authorization intelligence: predictable default secrets, debug defaults, demo mode bypasses, static OTP checks, unprotected admin routes, payment verification bypasses, permissive CORS, insecure sessions, and unsanitized file uploads.
4. **`semgrep`**: Multi-language static application security testing (SAST).
5. **`bandit`**: Python AST security analysis (CWEs, unsafe deserialization, SQL injection).
6. **`ruff`**: High-performance Python linting and code quality analysis.
7. **`eslint`**: JavaScript and TypeScript syntax and quality analysis.
8. **`npm-audit` & `pip-audit`**: Transitive dependency vulnerability checks against OSV / PyPI / npm advisories.

---

## 2. Invariants & Security Boundaries

- **Zero Untrusted Code Execution**: Never runs target code, build scripts, npm lifecycle hooks, or application entry points.
- **Deterministic Fingerprinting**: All findings generate SHA-256 fingerprints across re-scans for stable matching.
- **Redaction by Default**: Secrets in code evidence are replaced with `[REDACTED_SECRET]` before storage or AI enrichment.
- **Authoritative Mathematical Scoring**: AI is strictly for explanation and remediation; scores are derived from mathematical formulas across 6 evaluation pillars.

