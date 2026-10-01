"""Project discovery, language identification, and essentials detection."""

import os
from pathlib import Path
from typing import List, Set
from rokospy_analyzer.config import config
from rokospy_analyzer.filtering.file_filter import FileFilter
from rokospy_analyzer.models.discovery import ProjectDiscovery


class ProjectDetector:
    """Inspects a repository workspace to discover languages, manifests, frameworks, and essentials."""

    JS_EXTENSIONS = {".js", ".mjs", ".cjs", ".jsx"}
    TS_EXTENSIONS = {".ts", ".tsx", ".mts", ".cts"}
    PYTHON_EXTENSIONS = {".py", ".pyw"}

    MANIFEST_FILENAMES = {
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "requirements.txt",
        "pyproject.toml",
        "Pipfile",
        "Pipfile.lock",
        "setup.py",
        "poetry.lock",
    }

    README_FILENAMES = {"readme.md", "readme.rst", "readme.txt", "readme"}
    GITIGNORE_FILENAMES = {".gitignore"}
    ENV_EXAMPLE_FILENAMES = {".env.example", ".env.sample", ".env.template", "example.env"}
    LICENSE_FILENAMES = {"license", "license.md", "license.txt", "licence", "licence.md"}

    @classmethod
    def inspect(cls, workspace_path: Path, project_name: str, source_type: str) -> ProjectDiscovery:
        """Inspects the workspace and constructs a ProjectDiscovery instance."""
        workspace_path = workspace_path.resolve()
        analyzable_files = FileFilter.collect_analyzable_files(workspace_path)

        languages_detected: Set[str] = set()
        manifests_found: Set[str] = set()
        frameworks: Set[str] = set()

        has_readme = False
        has_gitignore = False
        has_env_example = False
        has_license = False
        has_tests = False

        relative_file_paths: List[str] = []
        total_size = 0

        for file_path in analyzable_files:
            rel_str = str(file_path.relative_to(workspace_path)).replace("\\", "/")
            relative_file_paths.append(rel_str)

            try:
                total_size += file_path.stat().st_size
            except OSError:
                pass

            lower_name = file_path.name.lower()
            ext = file_path.suffix.lower()

            # Language detection
            if ext in cls.JS_EXTENSIONS:
                languages_detected.add("JavaScript")
            elif ext in cls.TS_EXTENSIONS:
                languages_detected.add("TypeScript")
            elif ext in cls.PYTHON_EXTENSIONS:
                languages_detected.add("Python")

            # Manifest detection
            if lower_name in cls.MANIFEST_FILENAMES:
                manifests_found.add(file_path.name)

            # Essentials detection
            if lower_name in cls.README_FILENAMES:
                has_readme = True
            if lower_name in cls.GITIGNORE_FILENAMES:
                has_gitignore = True
            if lower_name in cls.ENV_EXAMPLE_FILENAMES:
                has_env_example = True
            if lower_name in cls.LICENSE_FILENAMES:
                has_license = True

            # Test files detection
            if (
                lower_name.startswith("test_")
                or lower_name.endswith("_test.py")
                or ".test." in lower_name
                or ".spec." in lower_name
                or "tests/" in rel_str.lower()
                or "test/" in rel_str.lower()
                or "__tests__/" in rel_str.lower()
            ):
                has_tests = True

            # Framework detection heuristics (lightweight static inspection)
            if lower_name == "package.json":
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    if "next" in content:
                        frameworks.add("Next.js")
                    if "react" in content:
                        frameworks.add("React")
                    if "express" in content:
                        frameworks.add("Express")
                    if "fastify" in content:
                        frameworks.add("Fastify")
                    if "vue" in content:
                        frameworks.add("Vue")
                except Exception:
                    pass

            if lower_name in {"requirements.txt", "pyproject.toml", "pipfile"}:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    if "fastapi" in content.lower():
                        frameworks.add("FastAPI")
                    if "django" in content.lower():
                        frameworks.add("Django")
                    if "flask" in content.lower():
                        frameworks.add("Flask")
                except Exception:
                    pass

        has_git_history = (workspace_path / ".git").exists()

        # Sort for deterministic output
        sorted_languages = sorted(list(languages_detected))
        sorted_manifests = sorted(list(manifests_found))
        sorted_frameworks = sorted(list(frameworks))

        return ProjectDiscovery(
            project_name=project_name,
            source_type=source_type,
            root_path=workspace_path,
            detected_languages=sorted_languages,
            manifests_found=sorted_manifests,
            frameworks=sorted_frameworks,
            all_files=relative_file_paths,
            total_file_count=len(relative_file_paths),
            total_size_bytes=total_size,
            has_git_history=has_git_history,
            has_readme=has_readme,
            has_gitignore=has_gitignore,
            has_env_example=has_env_example,
            has_license=has_license,
            has_tests=has_tests,
        )
