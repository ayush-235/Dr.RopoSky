"""Configuration constants, safety limits, and execution policies for Rokospy Analyzer."""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnalyzerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ROKOSPY_", env_file=".env", extra="ignore")

    # AI Configuration (Phase 2)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    AI_TIMEOUT_SECONDS: int = 30
    MAX_AI_FINDINGS_PER_SCAN: int = 25
    MAX_CONTEXT_LINES: int = 15
    MAX_CONTEXT_CHARS: int = 4000

    # Safety limits
    MAX_REPO_SIZE_MB: int = 100
    MAX_EXTRACTED_SIZE_MB: int = 300
    MAX_FILE_COUNT: int = 3000
    MAX_EVIDENCE_LINES: int = 10
    MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB per file for AST/regex parsing

    # Execution timeouts (seconds)
    GIT_CLONE_TIMEOUT_SECONDS: int = 60
    SCANNER_TIMEOUT_SECONDS: int = 90
    TOTAL_ANALYSIS_TIMEOUT_SECONDS: int = 300

    # Redaction token
    REDACTION_STRING: str = "[REDACTED_SECRET]"

    # Excluded directories
    EXCLUDED_DIRS: set[str] = {
        "node_modules",
        ".git",
        "dist",
        "build",
        "coverage",
        ".next",
        "out",
        "__pycache__",
        ".venv",
        "venv",
        "ENV",
        "env",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "vendor",
        ".idea",
        ".vscode",
    }

    # Binary/media extensions to ignore
    EXCLUDED_EXTENSIONS: set[str] = {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
        ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
        ".exe", ".dll", ".so", ".dylib", ".bin",
        ".mp3", ".mp4", ".mov", ".avi", ".webm",
        ".woff", ".woff2", ".ttf", ".eot",
        ".pyc", ".pyo", ".pyd",
    }


# Global default configuration instance
config = AnalyzerConfig()
