# Dr.RopoSky Backend (Phase 4)

FastAPI Backend & API Service Layer for Dr.RopoSky.

## Overview

The Dr.RopoSky Backend acts as a high-performance orchestration and API gateway over the standalone `rokospy-analyzer` pipeline. It exposes RESTful endpoints for initiating static and security scans, validating inputs against strict security policies, and delivering structured `AnalysisReport` JSON responses to the Next.js frontend.

## Architecture

```
Frontend (Next.js)
       ↓
FastAPI Backend (/api/v1)
       ↓
Analysis Orchestration Service (SSRF validation, tempfile lifecycle)
       ↓
Analyzer Pipeline (ManagedWorkspace -> Scanners -> Redactor -> AI -> Scoring)
       ↓
AnalysisReport (Pydantic Model)
```

## API Endpoints

### 1. Health Probe
- **Endpoint**: `GET /api/v1/health`
- **Response**: `200 OK`
```json
{
  "status": "ok",
  "service": "rokospy-backend",
  "version": "0.1.0"
}
```

### 2. Analyze Project
- **Endpoint**: `POST /api/v1/analyze`
- **Request (multipart/form-data)**:
  - `github_url` (optional string): Public HTTPS GitHub URL (e.g., `https://github.com/owner/repo`)
  - `zip_file` (optional binary): Uploaded `.zip` archive (max 100 MB)
  - *Note: Exactly one source must be provided.*
- **Response**: `200 OK` with full `AnalysisReport` JSON.

### 3. Compare Reports (Phase 7 Progress Tracking)
- **Endpoint**: `POST /api/v1/compare`
- **Request (application/json)**:
  - `previous_report` (AnalysisReport object): Baseline scan report
  - `current_report` (AnalysisReport object): Re-scan report
- **Response**: `200 OK` with `ComparisonReport` JSON containing deterministic score progression (`overall`, `pillars`), finding diff categorization (`fixed_findings`, `new_findings`, `remaining_findings`, `changed_findings`), and progression `summary`.

### 4. API Documentation
- **Swagger UI**: `GET /api/v1/docs`
- **OpenAPI JSON**: `GET /api/v1/openapi.json`

## Security Controls

- **SSRF Defense**: Strict validation of `github_url` requiring HTTPS and host `github.com`. Loopback, internal/private IP ranges, non-standard ports, and embedded credentials are hard rejected.
- **Zip Slip & Path Traversal**: Extracted archive contents are sanitized against directory traversal attacks (`../`) and absolute paths.
- **Quota Enforcements**: Maximum 100 MB upload size, maximum 300 MB uncompressed, and maximum 3,000 files.
- **Zero Code Execution**: Untrusted project files are never executed. `setup.py`, `package.json` install scripts, and executable binaries are strictly treated as static text/data.
- **Deterministic Cleanup**: All uploaded temporary files and working extraction directories are safely deleted upon request completion.
- **Sanitized Error Responses**: Internal paths and stack traces are withheld from client responses.

## Environment Configuration

Configuration is loaded from environment variables or `backend/.env` (which must never be committed):

```env
GEMINI_API_KEY=your_gemini_api_key_here    # Optional: For AI explanation and fix steps
GEMINI_MODEL=gemini-2.5-flash              # Configurable Gemini model
ROKOSPY_BACKEND_HOST=0.0.0.0
ROKOSPY_BACKEND_PORT=8000
ROKOSPY_BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Running the Backend

```bash
# Start uvicorn development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing

```bash
# Run backend test suite
pytest backend/tests -v
```
