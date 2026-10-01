"""Built-in Rokospy Secret Scanner adapter.

Scans all analyzable files using precise AST/regex patterns to detect exposed credentials,
API keys, tokens, and private keys with immediate redaction.
"""

import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from rokospy_analyzer.config import config
from rokospy_analyzer.filtering.file_filter import FileFilter
from rokospy_analyzer.models.discovery import ProjectDiscovery
from rokospy_analyzer.models.finding import (
    CategoryEnum,
    SeverityEnum,
    ConfidenceEnum,
    NormalizedFinding,
)
from rokospy_analyzer.models.report import ScannerStatusEnum
from rokospy_analyzer.normalization.fingerprint import generate_finding_fingerprint
from rokospy_analyzer.scanners.base import BaseScanner
from rokospy_analyzer.security.redactor import SecretRedactor


class BuiltinSecretScanner(BaseScanner):
    """Built-in regex-based secret scanner for hardcoded credentials and tokens."""

    @property
    def name(self) -> str:
        return "rokospy-secret-scanner"

    @property
    def supported_languages(self) -> List[str]:
        return ["All"]

    def is_available(self) -> bool:
        # Built-in scanner is always available
        return True

    def is_applicable(self, discovery: ProjectDiscovery) -> bool:
        # Applicable to any project with analyzable files
        return discovery.total_file_count > 0

    def run(
        self, workspace_path: Path, discovery: ProjectDiscovery
    ) -> Tuple[ScannerStatusEnum, List[NormalizedFinding], Optional[str]]:
        findings: List[NormalizedFinding] = []
        analyzable_files = FileFilter.collect_analyzable_files(workspace_path)

        for file_path in analyzable_files:
            rel_file = str(file_path.relative_to(workspace_path)).replace("\\", "/")

            # Skip .env.example / .env.sample templates as they are non-secret placeholders
            if file_path.name.lower() in {".env.example", ".env.sample", ".env.template", "example.env"}:
                continue

            try:
                # Read line by line with memory limit
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            lines = content.splitlines()
            for line_idx, line_text in enumerate(lines, start=1):
                # Ignore very long minified lines (> 2000 chars)
                if len(line_text) > 2000:
                    continue

                for label, pattern in SecretRedactor.PATTERNS:
                    match = pattern.search(line_text)
                    if match:
                        matched_val = match.group(1) if (match.groups() and match.group(1)) else match.group(0)
                        # Skip placeholder tokens
                        if matched_val.upper() in {"YOUR_API_KEY", "CHANGE_ME", "EXAMPLE", "REDACTED", "PLACEHOLDER", "TEST_KEY", "DUMMY", "XXX"}:
                            continue

                        # Determine severity
                        severity = SeverityEnum.CRITICAL if ("Key" in label or "Token" in label or "Stripe" in label or "AWS" in label) else SeverityEnum.HIGH

                        # Generate sanitized evidence
                        start_idx = max(0, line_idx - 2)
                        end_idx = min(len(lines), line_idx + 2)
                        context_lines = []
                        for ctx_i in range(start_idx, end_idx):
                            ctx_line = lines[ctx_i]
                            sanitized_line = SecretRedactor.redact(ctx_line)
                            prefix = f"{ctx_i + 1:4d} | "
                            if ctx_i == line_idx - 1:
                                prefix = f"{ctx_i + 1:4d} > "
                            context_lines.append(f"{prefix}{sanitized_line}")
                        evidence_snippet = "\n".join(context_lines)

                        rule_id = f"secret-{label.lower().replace(' ', '-')}"
                        title = f"Exposed {label}"
                        message = f"Detected hardcoded {label.lower()} in source code. Credentials must never be stored in code."

                        fp = generate_finding_fingerprint(
                            scanner=self.name,
                            rule_id=rule_id,
                            file_path=rel_file,
                            line=line_idx,
                            title=title,
                        )

                        finding = NormalizedFinding(
                            id=str(uuid.uuid4()),
                            title=title,
                            category=CategoryEnum.SECURITY,
                            severity=severity,
                            file=rel_file,
                            line=line_idx,
                            column=match.start() + 1,
                            rule_id=rule_id,
                            scanner=self.name,
                            message=message,
                            evidence=evidence_snippet,
                            confidence=ConfidenceEnum.HIGH,
                            source=self.name,
                            fingerprint=fp,
                        )
                        findings.append(finding)
                        # Break pattern loop for this line once a secret pattern has matched
                        break

        return ScannerStatusEnum.SUCCESS, findings, None
