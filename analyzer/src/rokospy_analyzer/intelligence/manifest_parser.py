"""Manifest parser for detecting dependencies, frameworks, engines, and tools statically."""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any



class ManifestParser:
    """Parses project package manifests statically without executing package managers."""

    @classmethod
    def parse_workspace(cls, workspace_path: Path) -> Dict[str, Any]:
        """Inspects all discovered manifests in workspace and extracts structured dependency metadata."""
        direct_dependencies: Set[str] = set()
        frameworks: Set[str] = set()
        test_frameworks: Set[str] = set()
        db_orm: Set[str] = set()
        auth_mechanisms: Set[str] = set()
        lockfiles: List[str] = []

        # Check for lockfiles
        lockfile_candidates = [
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "poetry.lock",
            "Pipfile.lock",
            "requirements.lock",
        ]
        for candidate in lockfile_candidates:
            if (workspace_path / candidate).exists():
                lockfiles.append(candidate)

        # 1. Parse package.json
        pkg_json_path = workspace_path / "package.json"
        if pkg_json_path.exists():
            try:
                data = json.loads(pkg_json_path.read_text(encoding="utf-8", errors="ignore"))
                deps = {}
                if isinstance(data.get("dependencies"), dict):
                    deps.update(data["dependencies"])
                if isinstance(data.get("devDependencies"), dict):
                    deps.update(data["devDependencies"])

                for dep in deps.keys():
                    direct_dependencies.add(dep)
                    dep_lower = dep.lower()

                    # Frameworks
                    if dep_lower in {"next", "next.js"}:
                        frameworks.add("Next.js")
                    elif dep_lower == "react":
                        frameworks.add("React")
                    elif dep_lower == "express":
                        frameworks.add("Express")
                    elif dep_lower == "fastify":
                        frameworks.add("Fastify")
                    elif dep_lower in {"@nestjs/core", "nestjs"}:
                        frameworks.add("NestJS")
                    elif dep_lower in {"vue", "nuxt"}:
                        frameworks.add("Vue")

                    # Testing
                    if dep_lower in {"jest", "@types/jest"}:
                        test_frameworks.add("Jest")
                    elif dep_lower == "vitest":
                        test_frameworks.add("Vitest")
                    elif dep_lower == "mocha":
                        test_frameworks.add("Mocha")
                    elif dep_lower == "cypress":
                        test_frameworks.add("Cypress")
                    elif dep_lower in {"playwright", "@playwright/test"}:
                        test_frameworks.add("Playwright")

                    # DB / ORM
                    if dep_lower in {"prisma", "@prisma/client"}:
                        db_orm.add("Prisma")
                    elif dep_lower == "mongoose":
                        db_orm.add("Mongoose")
                    elif dep_lower == "typeorm":
                        db_orm.add("TypeORM")
                    elif dep_lower == "sequelize":
                        db_orm.add("Sequelize")
                    elif dep_lower in {"knex", "pg", "mysql2"}:
                        db_orm.add(dep)

                    # Auth
                    if dep_lower in {"jsonwebtoken", "jose"}:
                        auth_mechanisms.add("JWT")
                    elif dep_lower in {"next-auth", "@auth/core"}:
                        auth_mechanisms.add("NextAuth")
                    elif dep_lower == "passport":
                        auth_mechanisms.add("Passport")
                    elif dep_lower in {"bcrypt", "bcryptjs", "argon2"}:
                        auth_mechanisms.add("Bcrypt/Argon2")

            except Exception:
                pass

        # 2. Parse requirements.txt
        req_txt_path = workspace_path / "requirements.txt"
        if req_txt_path.exists():
            try:
                content = req_txt_path.read_text(encoding="utf-8", errors="ignore")
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue
                    # Extract pkg name (before ==, >=, <=, ~=, <, >)
                    match = re.match(r"^([a-zA-Z0-9_\-\.]+)", line)
                    if match:
                        dep = match.group(1).lower()
                        direct_dependencies.add(dep)

                        if dep == "fastapi":
                            frameworks.add("FastAPI")
                        elif dep == "django":
                            frameworks.add("Django")
                        elif dep == "flask":
                            frameworks.add("Flask")

                        if dep in {"pytest", "unittest"}:
                            test_frameworks.add("Pytest" if dep == "pytest" else "Unittest")

                        if dep in {"sqlalchemy"}:
                            db_orm.add("SQLAlchemy")
                        elif dep in {"tortoise-orm", "peewee", "psycopg2", "psycopg2-binary", "asyncpg", "pymongo", "motor"}:
                            db_orm.add(dep)

                        if dep in {"pyjwt", "python-jose"}:
                            auth_mechanisms.add("JWT")
                        elif dep in {"passlib", "bcrypt"}:
                            auth_mechanisms.add("Bcrypt/Passlib")
            except Exception:
                pass

        # 3. Parse pyproject.toml
        pyproject_path = workspace_path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                content = pyproject_path.read_text(encoding="utf-8", errors="ignore")
                content_lower = content.lower()
                if "fastapi" in content_lower:
                    frameworks.add("FastAPI")
                if "django" in content_lower:
                    frameworks.add("Django")
                if "flask" in content_lower:
                    frameworks.add("Flask")
                if "pytest" in content_lower:
                    test_frameworks.add("Pytest")
                if "sqlalchemy" in content_lower:
                    db_orm.add("SQLAlchemy")
            except Exception:
                pass


        return {
            "direct_dependencies": sorted(list(direct_dependencies)),
            "frameworks": sorted(list(frameworks)),
            "test_frameworks": sorted(list(test_frameworks)),
            "db_orm_detected": sorted(list(db_orm)),
            "auth_mechanisms_detected": sorted(list(auth_mechanisms)),
            "lockfile_names": lockfiles,
            "has_lockfile": len(lockfiles) > 0,
        }
