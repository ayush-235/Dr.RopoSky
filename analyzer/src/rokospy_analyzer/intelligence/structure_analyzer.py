"""Static code structure, routes, and environment variable cross-reference analyzer."""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from rokospy_analyzer.filtering.file_filter import FileFilter
from rokospy_analyzer.intelligence.models import RouteInfo, ProjectIntelligence
from rokospy_analyzer.intelligence.manifest_parser import ManifestParser


class StructureAnalyzer:
    """Performs static code structure discovery, AST route extraction, and cross-file env analysis."""

    # Regex for extracting environment variable reads in JS/TS
    JS_ENV_REGEX = re.compile(r"process\.env\.([A-Z0-9_]+)|process\.env\[['\"]([A-Z0-9_]+)['\"]\]|import\.meta\.env\.([A-Z0-9_]+)")
    # Regex for Python os.getenv / os.environ
    PY_ENV_REGEX = re.compile(r"os\.getenv\(['\"]([A-Z0-9_]+)['\"]|os\.environ\.get\(['\"]([A-Z0-9_]+)['\"]|os\.environ\[['\"]([A-Z0-9_]+)['\"]")

    ENTRY_POINT_CANDIDATES = {
        "main.py",
        "app.py",
        "server.py",
        "manage.py",
        "wsgi.py",
        "asgi.py",
        "index.js",
        "server.js",
        "app.js",
        "main.js",
        "index.ts",
        "server.ts",
        "app.ts",
        "main.ts",
        "app/page.tsx",
        "app/page.jsx",
        "app/page.js",
        "src/app/page.tsx",
        "src/index.tsx",
        "src/index.ts",
        "src/main.ts",
        "src/main.tsx",
        "src/App.tsx",
        "src/App.jsx",
    }

    @classmethod
    def analyze_workspace(cls, workspace_path: Path, project_name: str, source_type: str) -> ProjectIntelligence:
        """Runs full static structural analysis on the workspace."""
        analyzable_files = FileFilter.collect_analyzable_files(workspace_path)
        manifest_data = ManifestParser.parse_workspace(workspace_path)

        entry_points: List[str] = []
        routes_detected: List[RouteInfo] = []
        env_vars_used: Set[str] = set()
        env_vars_documented: Set[str] = set()
        test_files_count = 0

        # 1. Collect documented env variables from templates
        env_template_names = [".env.example", ".env.sample", ".env.template", "example.env"]
        for tmpl in env_template_names:
            tmpl_path = workspace_path / tmpl
            if tmpl_path.exists():
                try:
                    content = tmpl_path.read_text(encoding="utf-8", errors="ignore")
                    for line in content.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            var_name = line.split("=")[0].strip()
                            if var_name:
                                env_vars_documented.add(var_name)
                except Exception:
                    pass

        # 2. Inspect all source files
        for file_path in analyzable_files:
            rel_path = str(file_path.relative_to(workspace_path)).replace("\\", "/")
            rel_lower = rel_path.lower()
            file_name = file_path.name
            lower_name = file_name.lower()
            ext = file_path.suffix.lower()

            # Entry points
            if rel_path in cls.ENTRY_POINT_CANDIDATES or file_name in cls.ENTRY_POINT_CANDIDATES:
                entry_points.append(rel_path)

            # Test files
            if (
                lower_name.startswith("test_")
                or lower_name.endswith("_test.py")
                or ".test." in lower_name
                or ".spec." in lower_name
                or "tests/" in rel_lower
                or "test/" in rel_lower
                or "__tests__/" in rel_lower
            ):
                test_files_count += 1

            # Read source content for AST/regex inspection
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Extract env usages
            if ext in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
                for match in cls.JS_ENV_REGEX.finditer(content):
                    var = match.group(1) or match.group(2) or match.group(3)
                    if var and var not in {"NODE_ENV", "PORT"}:
                        env_vars_used.add(var)

            elif ext in {".py", ".pyw"}:
                for match in cls.PY_ENV_REGEX.finditer(content):
                    var = match.group(1) or match.group(2) or match.group(3)
                    if var:
                        env_vars_used.add(var)

                # Python AST route extraction
                cls._extract_python_routes(content, rel_path, routes_detected)

            # JS/TS Route Extraction heuristics (Express / Next.js)
            if ext in {".js", ".ts", ".jsx", ".tsx"}:
                cls._extract_js_routes(content, rel_path, routes_detected)

        # Calculate missing env vars
        missing_env_vars = sorted(list(env_vars_used - env_vars_documented))

        # Global auth detection
        has_global_auth = False
        for file_path in analyzable_files:
            try:
                txt = file_path.read_text(encoding="utf-8", errors="ignore")
                if (
                    re.search(r"add_middleware\s*\(\s*(?:[a-zA-Z0-9_]*Auth|[a-zA-Z0-9_]*JWT|[a-zA-Z0-9_]*Security)", txt, re.IGNORECASE)
                ) or (
                    re.search(r"app\.use\s*\(\s*(?:auth|passport|verifyToken|jwt)", txt, re.IGNORECASE)
                ):
                    has_global_auth = True
                    break
            except Exception:
                pass


        # Determine project type
        frameworks = manifest_data["frameworks"]
        has_frontend = any(f in {"Next.js", "React", "Vue"} for f in frameworks) or any("app/page." in p or "src/app/" in p or "src/components/" in p for p in entry_points)
        has_backend = any(f in {"FastAPI", "Django", "Flask", "Express", "NestJS", "Fastify"} for f in frameworks) or len(routes_detected) > 0

        if has_frontend and has_backend:
            project_type = "fullstack"
        elif has_backend:
            project_type = "backend_api"
        elif has_frontend:
            project_type = "frontend_spa"
        elif len(manifest_data["direct_dependencies"]) > 0:
            project_type = "library"
        elif len(entry_points) > 0:
            project_type = "script"
        else:
            project_type = "general"

        return ProjectIntelligence(
            project_type=project_type,
            frameworks=frameworks,
            entry_points=sorted(entry_points),
            routes_detected=routes_detected,
            env_vars_used=sorted(list(env_vars_used)),
            env_vars_documented=sorted(list(env_vars_documented)),
            missing_env_vars=missing_env_vars,
            direct_dependencies=manifest_data["direct_dependencies"],
            has_lockfile=manifest_data["has_lockfile"],
            lockfile_names=manifest_data["lockfile_names"],
            has_tests=test_files_count > 0 or len(manifest_data["test_frameworks"]) > 0,
            test_frameworks=manifest_data["test_frameworks"],
            test_files_count=test_files_count,
            db_orm_detected=manifest_data["db_orm_detected"],
            auth_mechanisms_detected=manifest_data["auth_mechanisms_detected"],
            has_global_auth=has_global_auth,
        )

    @classmethod
    def _extract_python_routes(cls, code: str, file_path: str, out_routes: List[RouteInfo]) -> None:
        """Parses Python AST to discover FastAPI, Flask, or Django routes and auth/permission boundaries."""
        try:
            tree = ast.parse(code)
        except Exception:
            return

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    # e.g., @app.get("/users"), @router.post("/auth/login")
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        attr_name = dec.func.attr.lower()
                        if attr_name in {"get", "post", "put", "delete", "patch", "options", "head"}:
                            route_path = "/"
                            if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                                route_path = dec.args[0].value

                            # Check for validation in args
                            has_val = False
                            has_auth = False
                            has_role_check = False
                            has_ownership_check = False

                            # Check decorator dependencies keyword (FastAPI dependencies=[Depends(...)])
                            for kw in dec.keywords:
                                if kw.arg == "dependencies":
                                    has_auth = True
                                    kw_dump = ast.dump(kw.value).lower()
                                    if "admin" in kw_dump or "role" in kw_dump or "superuser" in kw_dump:
                                        has_role_check = True

                            # Check additional function decorators (@login_required, @admin_required, etc.)
                            for other_dec in node.decorator_list:
                                dec_name = ""
                                if isinstance(other_dec, ast.Name):
                                    dec_name = other_dec.id.lower()
                                elif isinstance(other_dec, ast.Call) and isinstance(other_dec.func, ast.Name):
                                    dec_name = other_dec.func.id.lower()
                                elif isinstance(other_dec, ast.Attribute):
                                    dec_name = other_dec.attr.lower()
                                elif isinstance(other_dec, ast.Call) and isinstance(other_dec.func, ast.Attribute):
                                    dec_name = other_dec.func.attr.lower()

                                if any(a in dec_name for a in ["auth", "login", "jwt", "token", "user", "protect"]):
                                    has_auth = True
                                if any(r in dec_name for r in ["admin", "role", "permission", "superuser"]):
                                    has_role_check = True
                                    has_auth = True

                            # Check arguments for validation & auth dependencies
                            for arg in node.args.args:
                                if arg.annotation:
                                    has_val = True
                                    ann_dump = ast.dump(arg.annotation).lower()
                                    if any(k in ann_dump for k in ["user", "token", "auth", "security", "credentials", "header"]):
                                        has_auth = True
                                    if any(k in ann_dump for k in ["admin", "superuser", "role"]):
                                        has_role_check = True
                                        has_auth = True

                            # Check function body for role & ownership checks
                            body_dump = ast.dump(node).lower()
                            if any(r in body_dump for r in ["role", "is_admin", "admin_required", "check_permission", "is_superuser"]):
                                has_role_check = True
                            if any(o in body_dump for o in ["user_id", "owner", "user.id", "current_user.id"]):
                                has_ownership_check = True

                            path_lower = route_path.lower()
                            is_admin = any(kw in path_lower for kw in ["/admin", "/management", "/internal", "manage", "system/reset", "superuser"])
                            is_payment = any(kw in path_lower for kw in ["payment", "checkout", "order", "refund", "verify", "transaction", "webhook", "payout"])
                            is_sensitive = is_admin or is_payment or any(kw in path_lower for kw in ["profile", "account", "password", "delete", "destroy", "settings", "users/"])

                            out_routes.append(
                                RouteInfo(
                                    method=attr_name.upper(),
                                    path=route_path,
                                    file=file_path,
                                    line=node.lineno,
                                    has_validation=has_val,
                                    has_auth=has_auth,
                                    has_role_check=has_role_check,
                                    has_ownership_check=has_ownership_check,
                                    is_sensitive=is_sensitive,
                                    is_admin=is_admin,
                                    is_payment=is_payment,
                                    handler_name=node.name,
                                )
                            )

    @classmethod
    def _extract_js_routes(cls, code: str, file_path: str, out_routes: List[RouteInfo]) -> None:
        """Extracts Express/Next.js routes and auth middleware boundaries."""
        # Express route pattern: app.get('/path', authMiddleware, handler) or router.post(...)
        express_pattern = re.compile(
            r"(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*([a-zA-Z0-9_]+))?",
            re.IGNORECASE,
        )
        for match in express_pattern.finditer(code):
            method = match.group(1).upper()
            route_path = match.group(2)
            middleware = (match.group(3) or "").lower()
            line_no = code[:match.start()].count("\n") + 1

            has_auth = any(k in middleware for k in ["auth", "jwt", "verify", "token", "protect", "login", "user"])
            has_role = any(k in middleware for k in ["admin", "role", "permission", "superuser"])
            if has_role:
                has_auth = True

            path_lower = route_path.lower()
            is_admin = any(kw in path_lower for kw in ["/admin", "/management", "/internal", "manage", "system/reset", "superuser"])
            is_payment = any(kw in path_lower for kw in ["payment", "checkout", "order", "refund", "verify", "transaction", "webhook", "payout"])
            is_sensitive = is_admin or is_payment or any(kw in path_lower for kw in ["profile", "account", "password", "delete", "destroy", "settings", "users/"])

            out_routes.append(
                RouteInfo(
                    method=method,
                    path=route_path,
                    file=file_path,
                    line=line_no,
                    has_validation=False,
                    has_auth=has_auth,
                    has_role_check=has_role,
                    has_ownership_check=False,
                    is_sensitive=is_sensitive,
                    is_admin=is_admin,
                    is_payment=is_payment,
                    handler_name=None,
                )
            )

        # Next.js Route Handler: export async function GET(request) or POST
        if "route.ts" in file_path or "route.js" in file_path:
            next_handler_pattern = re.compile(r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH)\s*\(", re.IGNORECASE)
            for match in next_handler_pattern.finditer(code):
                method = match.group(1).upper()
                line_no = code[:match.start()].count("\n") + 1
                has_auth = "auth" in code.lower() or "session" in code.lower() or "getserversession" in code.lower()
                has_role = "admin" in code.lower() or "role" in code.lower()

                path_lower = file_path.lower()
                is_admin = any(kw in path_lower for kw in ["admin", "management", "internal"])
                is_payment = any(kw in path_lower for kw in ["payment", "checkout", "order", "refund", "verify"])
                is_sensitive = is_admin or is_payment or any(kw in path_lower for kw in ["profile", "account", "password", "delete"])

                out_routes.append(
                    RouteInfo(
                        method=method,
                        path=file_path,
                        file=file_path,
                        line=line_no,
                        has_validation=False,
                        has_auth=has_auth,
                        has_role_check=has_role,
                        has_ownership_check=False,
                        is_sensitive=is_sensitive,
                        is_admin=is_admin,
                        is_payment=is_payment,
                        handler_name=method,
                    )
                )

