"""Context extraction and secret sanitization for AI enrichment."""

from pathlib import Path
from rokospy_analyzer.ai.models import AIContextData
from rokospy_analyzer.config import config
from rokospy_analyzer.models.discovery import ProjectDiscovery
from rokospy_analyzer.models.finding import NormalizedFinding
from rokospy_analyzer.security.redactor import SecretRedactor


class ContextExtractor:
    """Safely extracts bounded source code snippets and sanitizes all context before AI consumption."""

    @classmethod
    def extract_context(
        cls, finding: NormalizedFinding, workspace_path: Path, discovery: ProjectDiscovery
    ) -> AIContextData:
        """
        Builds a sanitized, bounded AIContextData payload for a given finding.
        Guarantees that SecretRedactor runs on all surrounding source code and metadata.
        """
        surrounding_code = ""
        target_file = workspace_path / finding.file

        if target_file.exists() and target_file.is_file() and finding.line > 0:
            try:
                raw_text = target_file.read_text(encoding="utf-8", errors="ignore")
                lines = raw_text.splitlines()
                total_lines = len(lines)

                half_window = config.MAX_CONTEXT_LINES // 2
                start_line = max(1, finding.line - half_window)
                end_line = min(total_lines, finding.line + half_window)

                formatted_lines = []
                for idx in range(start_line - 1, end_line):
                    line_num = idx + 1
                    line_content = lines[idx]
                    # Truncate minified / excessively long lines
                    if len(line_content) > 300:
                        line_content = line_content[:300] + " ... [truncated]"
                    prefix = f"{line_num:4d} > " if line_num == finding.line else f"{line_num:4d} | "
                    formatted_lines.append(f"{prefix}{line_content}")

                extracted_block = "\n".join(formatted_lines)
                # Enforce char limit
                if len(extracted_block) > config.MAX_CONTEXT_CHARS:
                    extracted_block = extracted_block[:config.MAX_CONTEXT_CHARS] + "\n... [context truncated]"

                # Mandatory Secret Redaction
                surrounding_code = SecretRedactor.redact(extracted_block)

            except Exception:
                surrounding_code = "[Source code could not be extracted]"

        # Secondary language detection for the specific file
        file_ext = Path(finding.file).suffix.lower()
        lang = "Unknown"
        if file_ext in {".py", ".pyw"}:
            lang = "Python"
        elif file_ext in {".ts", ".tsx"}:
            lang = "TypeScript"
        elif file_ext in {".js", ".jsx", ".mjs", ".cjs"}:
            lang = "JavaScript"
        elif discovery.detected_languages:
            lang = discovery.detected_languages[0]

        # Sanitized finding fields
        clean_title = SecretRedactor.redact(finding.title)
        clean_message = SecretRedactor.redact(finding.message)
        clean_evidence = SecretRedactor.redact(finding.evidence)

        return AIContextData(
            finding_id=finding.id,
            title=clean_title,
            category=finding.category.value if hasattr(finding.category, "value") else str(finding.category),
            severity=finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity),
            file=finding.file,
            line=finding.line,
            rule_id=finding.rule_id,
            scanner=finding.scanner,
            message=clean_message,
            evidence=clean_evidence,
            surrounding_code=surrounding_code,
            project_name=discovery.project_name,
            language=lang,
            frameworks=discovery.frameworks,
        )
