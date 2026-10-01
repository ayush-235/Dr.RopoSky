-- ==========================================================
-- Dr.RopoSky — Supabase PostgreSQL Initial Schema
-- Migration 001: Projects, Scans, Findings, Scan Comparisons
-- ==========================================================

-- 1. Projects Table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,  -- 'github', 'zip', 'local'
    source_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Scans Table
CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'completed',  -- 'completed', 'failed', 'running'
    overall_score INT NOT NULL,
    security_score INT NOT NULL,
    reliability_score INT NOT NULL,
    quality_score INT NOT NULL,
    performance_score INT NOT NULL,
    architecture_score INT NOT NULL,
    completeness_score INT NOT NULL,
    total_findings INT NOT NULL DEFAULT 0,
    critical_count INT NOT NULL DEFAULT 0,
    high_count INT NOT NULL DEFAULT 0,
    medium_count INT NOT NULL DEFAULT 0,
    low_count INT NOT NULL DEFAULT 0,
    info_count INT NOT NULL DEFAULT 0,
    raw_report JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Findings Table
CREATE TABLE IF NOT EXISTS findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    fingerprint TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INT,
    why_it_matters TEXT,
    fix_steps JSONB,
    code_before TEXT,
    code_after TEXT,
    confidence NUMERIC,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Scan Comparisons Table
CREATE TABLE IF NOT EXISTS scan_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    previous_scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    current_scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    score_delta INT NOT NULL,
    security_delta INT NOT NULL,
    reliability_delta INT NOT NULL,
    quality_delta INT NOT NULL,
    performance_delta INT NOT NULL,
    architecture_delta INT NOT NULL,
    completeness_delta INT NOT NULL,
    fixed_count INT NOT NULL DEFAULT 0,
    new_count INT NOT NULL DEFAULT 0,
    remaining_count INT NOT NULL DEFAULT 0,
    changed_count INT NOT NULL DEFAULT 0,
    raw_comparison JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_projects_source_url ON projects(source_url);
CREATE INDEX IF NOT EXISTS idx_scans_project_id ON scans(project_id);
CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_findings_scan_id ON findings(scan_id);
CREATE INDEX IF NOT EXISTS idx_findings_fingerprint ON findings(fingerprint);
CREATE INDEX IF NOT EXISTS idx_scan_comparisons_project_id ON scan_comparisons(project_id);
CREATE INDEX IF NOT EXISTS idx_scan_comparisons_current_scan_id ON scan_comparisons(current_scan_id);
