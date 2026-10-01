# Dr.RopoSky

> **Find what’s wrong with your project.**  
> AI-powered software project auditor for security, reliability, quality, performance, architecture, and completeness.

---

## 1. Overview

**Dr.RopoSky** is an automated software project auditing platform designed for students, beginner developers, freelancers, hackathon teams, and solo creators. A user submits a public or private GitHub repository URL or uploads a project ZIP archive. Dr.RopoSky performs comprehensive static code and cybersecurity analysis without executing untrusted application code, explains findings with actionable remediation steps via an AI intelligence layer, and computes a deterministic project health score.

---

## 2. The Problem & The Solution

### The Problem
- Traditional linters output noisy, disconnected terminal warnings without business impact or fix context.
- Existing security tools are complex, expensive, and geared towards enterprise DevSecOps teams rather than individual builders.
- Developers often do not know *why* a pattern is unsafe or *how* to refactor it securely without breaking functionality.

### The Dr.RopoSky Solution
- **Ground-Truth Static Analysis**: Real vulnerabilities detected by battle-tested tools (Semgrep, Gitleaks, Bandit, Ruff, ESLint, dependency audits).
- **Educational AI Intelligence**: An abstracted AI layer (Gemini) enriches verified findings with plain-English impact analysis, step-by-step fix guides, and before/after code snippets.
- **Deterministic Scoring**: Transparent, reproducible scoring (0–100) across 6 core pillars.
- **Re-Scan Verification**: Quantifies improvements across iterations (Previous vs. New Score, fixed/remaining/new issues).

---

## 3. Core Cybersecurity Capabilities

Cybersecurity is a first-class module in Dr.RopoSky. The platform detects:
- **Exposed Credentials & Hardcoded Keys**: API keys, database credentials, authentication tokens.
- **Injection Vulnerabilities**: SQL injection, Command injection, and unsafe shell execution.
- **Web Vulnerabilities**: Cross-Site Scripting (XSS), Server-Side Request Forgery (SSRF), Path traversal.
- **Unsafe Code Execution**: Insecure deserialization, dangerous `eval()` / `exec()` calls.
- **Dependency CVEs**: Known vulnerabilities in npm and Python packages.
- **Configuration Weaknesses**: Insecure CORS policies, exposed debug configurations, missing security headers.

> **Zero Secret Exposure Policy**: Raw secrets are immediately redacted (`[REDACTED_SECRET]`) and never stored in plain text, logged, sent to AI prompts, or rendered in the UI.

---

## 4. Core Security Rule: Zero Untrusted Code Execution

**Dr.RopoSky NEVER executes submitted application code.**
- Analyzers operate exclusively via static inspection, AST parsing, and rule matching.
- The system will never run `npm start`, execute target Python scripts, trigger build lifecycle hooks (`postinstall`), or run untrusted Makefiles/Dockerfiles.
- Analysis subprocesses run in isolated sandboxes with strict execution timeouts, CPU/memory limits, read-only filesystem access, and disabled outbound networking.

---

## 5. System Architecture

```text
Repository / ZIP
       │
       ▼
[ Acquisition & Validation ]
       │
       ▼
[ Project Inspection & Workspace Pruning ]
       │
       ▼
[ Static & Security Analyzers ] ── (Semgrep, Bandit, Ruff, ESLint, Gitleaks, Audits)
       │
       ▼
[ Normalized Findings & Secret Redactor ]
       │
       ▼
[ AI Intelligence Layer ] ── (AIProvider Interface -> GeminiProvider)
       │
       ▼
[ Deterministic Scoring Engine ] ── (6 Pillars: Security, Reliability, Quality, Performance, Arch, Essentials)
       │
       ▼
[ Audit Report & Re-scan Diff Engine ] ── (Next.js Dashboard + 3D Landing Experience)
```

---

## 6. Technology Stack

- **Analyzer Engine**: Python 3.11+, Pydantic v2, Semgrep, Bandit, Ruff, ESLint, Gitleaks, npm-audit, pip-audit.
- **AI Layer**: Google Gemini API (via official Google GenAI SDK behind `AIProvider` abstraction).
- **Scoring Engine**: Pure mathematical deterministic 6-pillar scoring engine.
- **Backend Service**: FastAPI, Uvicorn, Pydantic, Supabase / PostgreSQL.
- **Frontend Application**: Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui, Monaco Editor, Recharts, Three.js / React Three Fiber.

---

## 7. Development Roadmap & Status

### Status Legend
- `[✓] IMPLEMENTED`: Completed and validated in the codebase.
- `[●] PLANNED`: Current active roadmap phase.
- `[○] FUTURE`: Post-hackathon scaling features.

| Phase | Milestone | Status | Description |
| :--- | :--- | :--- | :--- |
| **Phase 0** | **Foundation & Control** | `[✓] IMPLEMENTED` | Verified workspace, synchronized specifications, `.env.example`, `.gitignore`, monorepo skeleton. |
| **Phase 1** | **Core Analyzer** | `[✓] IMPLEMENTED` | Standalone Python static/security engine (Semgrep, Bandit, Ruff, Gitleaks, Redactor, CLI runner). |
| **Phase 2** | **AI Intelligence Layer** | `[✓] IMPLEMENTED` | `AIProvider` interface, Gemini integration, prompt injection defense, structured JSON validation, fix generation. |
| **Phase 3** | **Deterministic Scoring** | `[✓] IMPLEMENTED` | 6-pillar mathematical scoring engine, unified report generator with schema versioning. |
| **Phase 4** | **FastAPI Backend** | `[✓] IMPLEMENTED` | REST API, scan stage job manager, temporary workspace lifecycle, SSRF defense, async execution. |
| **Phase 5** | **Next.js & 3D Landing** | `[✓] IMPLEMENTED` | Minimal dark developer UI, 3D Project Analysis Core, Monaco code viewer, dashboard. |
| **Phase 6** | **Cybersecurity Center**| `[✓] IMPLEMENTED` | Dedicated vulnerability command center, rotation & revocation guidance, scanner coverage. |
| **Phase 7** | **Re-scan Engine** | `[✓] IMPLEMENTED` | Differential scan comparison, progress timeline, measurable score deltas, deterministic diffing. |
| **Phase 8** | **Deployment Hardening**| `[●] PLANNED` | Containerization, Vercel frontend deployment, Render/Railway backend hosting. |
| **Phase 9** | **Demo Optimization** | `[●] PLANNED` | Curated sample repositories, 2-4 minute live presentation flow. |
| **Phase 10+**| **Production SaaS** | `[○] FUTURE` | GitHub OAuth, persistent multi-user history, Celery/Redis queues, GitHub App, PR bots. |

---

## 8. Current Phase

**Phase 7 (Re-scan & Progress Tracking) is COMPLETE.**  
Next Phase: **Phase 8 (Deployment Hardening & Production Packaging)**.

---

## 9. Environment Configuration
 
Dr.RopoSky uses localized environment files that must never be committed to source control:
- **Backend (`backend/.env`)**:
  ```env
  GEMINI_API_KEY=your-api-key-here      # Optional for static scans, required for AI explanations
  GEMINI_MODEL=gemini-2.5-flash        # Configurable Gemini model identifier
  ROKOSPY_BACKEND_PORT=8000
  ROKOSPY_BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
  ```
- **Frontend (`frontend/.env.local`)**:
  ```env
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```
 
---
 
## 10. Local Prerequisites & CLI Usage
 
- **Python**: `3.11+`
- **Node.js**: `v20+`
- **Git**: `2.40+`
 
### Running the Standalone Analyzer with Scoring:
```bash
# Analyze a local project directory (computes score and displays category breakdown)
python -m rokospy_analyzer.cli analyze ./my-project

# Analyze a ZIP archive and save structured JSON
python -m rokospy_analyzer.cli analyze ./project.zip --output report.json

# Analyze a public GitHub repository
python -m rokospy_analyzer.cli analyze https://github.com/owner/repo
```
