"""Static architecture, coupling, and layer boundary analyzer."""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from rokospy_analyzer.filtering.file_filter import FileFilter
from rokospy_analyzer.models.finding import (
    CategoryEnum,
    SeverityEnum,
    ConfidenceEnum,
    NormalizedFinding,
)
from rokospy_analyzer.normalization.fingerprint import FindingFingerprint


class ArchitectureAnalyzer:
    """Analyzes architecture topology, God modules, scattered configuration, and layer boundaries."""

    MAX_MODULE_LOC_THRESHOLD = 500

    NODE_SERVER_MODULES = {
        "child_process",
        "fs",
        "fs/promises",
        "cluster",
        "dgram",
        "dns",
        "net",
        "tls",
        "v8",
        "vm",
    }

    COMMAND_INJECTION_REGEX_PY = re.compile(
        r"(?:os\.system|subprocess\.Popen|subprocess\.run|subprocess\.call)\s*\(\s*(?:f['\"][^'\"]*\{|['\"][^'\"]*\s*%\s*|[a-zA-Z0-9_]+\s*\+)",
        re.IGNORECASE,
    )
    COMMAND_INJECTION_REGEX_JS = re.compile(
        r"(?:exec|execSync|spawn|spawnSync)\s*\(\s*(?:`[^`]*\$\{|['\"][^'\"]*\s*\+)",
        re.IGNORECASE,
    )

    RAW_SQL_CONCAT_REGEX = re.compile(
        r"(?:cursor\.execute|db\.query|db\.execute|query)\s*\(\s*(?:f['\"]SELECT|f['\"]INSERT|f['\"]UPDATE|f['\"]DELETE|['\"]SELECT[^'\"]*['\"]\s*\+|`SELECT[^`]*\$\{)",
        re.IGNORECASE,
    )

    @classmethod
    def analyze_workspace(cls, workspace_path: Path) -> List[NormalizedFinding]:
        """Runs deterministic architectural & structural vulnerability analysis across workspace."""
        analyzable_files = FileFilter.collect_analyzable_files(workspace_path)
        findings: List[NormalizedFinding] = []

        env_read_files: Set[str] = set()
        has_config_module = False

        for file_path in analyzable_files:
            rel_path = str(file_path.relative_to(workspace_path)).replace("\\", "/")
            lower_rel = rel_path.lower()
            ext = file_path.suffix.lower()

            if "config." in lower_rel or "env." in lower_rel or "settings." in lower_rel:
                has_config_module = True

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            lines = content.splitlines()
            loc = len(lines)

            # 1. God Module / Excessive Module Size (> 500 lines)
            if loc > cls.MAX_MODULE_LOC_THRESHOLD and not lower_rel.endswith(".json") and not lower_rel.endswith(".lock"):
                fp = FindingFingerprint.generate("rokospy-arch", "excessive-module-size", rel_path, 1)
                findings.append(
                    NormalizedFinding(
                        id=fp,
                        title=f"Excessive Module Size ({loc} LOC)",
                        category=CategoryEnum.ARCHITECTURE,
                        severity=SeverityEnum.LOW,
                        file=rel_path,
                        file_path=rel_path,
                        line=1,
                        line_number=1,
                        column=0,
                        column_number=0,
                        rule_id="excessive-module-size",
                        scanner="rokospy-architecture",
                        message=f"Module `{rel_path}` contains {loc} lines of code, exceeding the architectural maintainability threshold of {cls.MAX_MODULE_LOC_THRESHOLD} LOC. Consider decomposing into focused sub-modules.",
                        evidence=f"File length: {loc} lines of code",
                        confidence=ConfidenceEnum.HIGH,
                        source="rokospy-architecture",
                        fingerprint=fp,
                    )
                )

            # 2. Track direct environment variable access for scattered config check
            if "os.getenv(" in content or "os.environ" in content or "process.env" in content:
                if "config" not in lower_rel and "setting" not in lower_rel:
                    env_read_files.add(rel_path)

            # 3. Layer Boundary Violation (Frontend importing Node server internals)
            is_frontend_file = (
                ("components/" in lower_rel or "pages/" in lower_rel or "app/" in lower_rel or "src/ui/" in lower_rel)
                and (ext in {".jsx", ".tsx", ".vue", ".svelte"})
            )
            if is_frontend_file:
                for line_idx, line in enumerate(lines, start=1):
                    for server_mod in cls.NODE_SERVER_MODULES:
                        if f"import" in line and (f"'{server_mod}'" in line or f'"{server_mod}"' in line or f"'node:{server_mod}'" in line):
                            fp = FindingFingerprint.generate("rokospy-arch", "layer-boundary-violation", rel_path, line_idx)
                            findings.append(
                                NormalizedFinding(
                                    id=fp,
                                    title=f"Layer Boundary Violation: Server Module in Frontend ({server_mod})",
                                    category=CategoryEnum.ARCHITECTURE,
                                    severity=SeverityEnum.MEDIUM,
                                    file=rel_path,
                                    file_path=rel_path,
                                    line=line_idx,
                                    line_number=line_idx,
                                    column=0,
                                    column_number=0,
                                    rule_id="layer-boundary-violation",
                                    scanner="rokospy-architecture",
                                    message=f"Frontend component `{rel_path}` directly imports server-only module `{server_mod}`. This can leak backend internals and cause client bundle runtime failures.",
                                    evidence=line.strip(),
                                    confidence=ConfidenceEnum.HIGH,
                                    source="rokospy-architecture",
                                    fingerprint=fp,
                                )
                            )

            # 4. Command Injection AST/Pattern Check
            for line_idx, line in enumerate(lines, start=1):
                if ext in {".py", ".pyw"} and cls.COMMAND_INJECTION_REGEX_PY.search(line):
                    fp = FindingFingerprint.generate("rokospy-arch", "insecure-command-execution", rel_path, line_idx)
                    findings.append(
                        NormalizedFinding(
                            id=fp,
                            title="Insecure Command Execution (Dynamic String)",
                            category=CategoryEnum.SECURITY,
                            severity=SeverityEnum.HIGH,
                            file=rel_path,
                            file_path=rel_path,
                            line=line_idx,
                            line_number=line_idx,
                            column=0,
                            column_number=0,
                            rule_id="insecure-command-execution",
                            scanner="rokospy-architecture",
                            message="Dynamic string concatenation or formatting inside system command execution (`os.system` / `subprocess`). Attackers supplying input to this parameter can achieve arbitrary command injection.",
                            evidence=line.strip(),
                            confidence=ConfidenceEnum.HIGH,
                            source="rokospy-architecture",
                            fingerprint=fp,
                        )
                    )

                if ext in {".js", ".ts", ".jsx", ".tsx"} and cls.COMMAND_INJECTION_REGEX_JS.search(line):
                    fp = FindingFingerprint.generate("rokospy-arch", "insecure-command-execution", rel_path, line_idx)
                    findings.append(
                        NormalizedFinding(
                            id=fp,
                            title="Insecure Command Execution (Dynamic String)",
                            category=CategoryEnum.SECURITY,
                            severity=SeverityEnum.HIGH,
                            file=rel_path,
                            file_path=rel_path,
                            line=line_idx,
                            line_number=line_idx,
                            column=0,
                            column_number=0,
                            rule_id="insecure-command-execution",
                            scanner="rokospy-architecture",
                            message="Dynamic template literal or concatenation inside `child_process.exec`. Unsanitized user inputs may allow remote command execution.",
                            evidence=line.strip(),
                            confidence=ConfidenceEnum.HIGH,
                            source="rokospy-architecture",
                            fingerprint=fp,
                        )
                    )

                # 5. Raw SQL concatenation
                if cls.RAW_SQL_CONCAT_REGEX.search(line):
                    fp = FindingFingerprint.generate("rokospy-arch", "raw-sql-concatenation", rel_path, line_idx)
                    findings.append(
                        NormalizedFinding(
                            id=fp,
                            title="SQL Injection Risk: Unparameterized Query String",
                            category=CategoryEnum.SECURITY,
                            severity=SeverityEnum.HIGH,
                            file=rel_path,
                            file_path=rel_path,
                            line=line_idx,
                            line_number=line_idx,
                            column=0,
                            column_number=0,
                            rule_id="raw-sql-concatenation",
                            scanner="rokospy-architecture",
                            message="SQL query constructed via string interpolation or formatting rather than parameterized placeholders. This allows SQL injection vulnerabilities.",
                            evidence=line.strip(),
                            confidence=ConfidenceEnum.HIGH,
                            source="rokospy-architecture",
                            fingerprint=fp,
                        )
                    )

        # 6. Scattered Configuration Check (> 4 disparate files directly reading environment without central config)
        if len(env_read_files) >= 5 and not has_config_module:
            fp = FindingFingerprint.generate("rokospy-arch", "scattered-env-config", "architecture", 1)
            sample_files = ", ".join(sorted(list(env_read_files))[:3])
            findings.append(
                NormalizedFinding(
                    id=fp,
                    title=f"Scattered Environment Configuration ({len(env_read_files)} modules)",
                    category=CategoryEnum.ARCHITECTURE,
                    severity=SeverityEnum.LOW,
                    file="architecture",
                    file_path="architecture",
                    line=1,
                    line_number=1,
                    column=0,
                    column_number=0,
                    rule_id="scattered-env-config",
                    scanner="rokospy-architecture",
                    message=f"Environment variables are read directly across {len(env_read_files)} distinct files ({sample_files}...) without a centralized configuration management layer. This leads to configuration drift and hidden dependencies.",
                    evidence=f"Direct env reads detected in {len(env_read_files)} files without central config schema",
                    confidence=ConfidenceEnum.HIGH,
                    source="rokospy-architecture",
                    fingerprint=fp,
                )
            )

        return findings
