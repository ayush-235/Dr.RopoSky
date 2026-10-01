"""Finding deduplication and normalization engine."""

from typing import List, Dict
from rokospy_analyzer.models.finding import NormalizedFinding, SeverityEnum


class FindingDeduplicator:
    """Deduplicates overlapping scanner findings and ensures deterministic ordering."""

    SEVERITY_WEIGHT = {
        SeverityEnum.CRITICAL: 5,
        SeverityEnum.HIGH: 4,
        SeverityEnum.MEDIUM: 3,
        SeverityEnum.LOW: 2,
        SeverityEnum.INFO: 1,
    }

    @classmethod
    def deduplicate(cls, findings: List[NormalizedFinding]) -> List[NormalizedFinding]:
        """
        Deduplicates findings based on fingerprint and normalized (file, line, category) locations.
        Merges duplicates by retaining the highest severity finding.
        """
        unique_by_fp: Dict[str, NormalizedFinding] = {}

        for finding in findings:
            fp = finding.fingerprint
            if fp not in unique_by_fp:
                unique_by_fp[fp] = finding
            else:
                existing = unique_by_fp[fp]
                # If current finding has higher severity, replace
                if cls.SEVERITY_WEIGHT.get(finding.severity, 0) > cls.SEVERITY_WEIGHT.get(existing.severity, 0):
                    unique_by_fp[fp] = finding

        # Secondary pass: Deduplicate same file + line + category (e.g. secret scanner & gitleaks on same line)
        location_map: Dict[str, NormalizedFinding] = {}
        for finding in unique_by_fp.values():
            loc_key = f"{finding.file}:{finding.line}:{finding.category}"
            if loc_key not in location_map:
                location_map[loc_key] = finding
            else:
                existing = location_map[loc_key]
                # If both are security secrets or same category, keep the highest severity
                if cls.SEVERITY_WEIGHT.get(finding.severity, 0) > cls.SEVERITY_WEIGHT.get(existing.severity, 0):
                    location_map[loc_key] = finding

        deduped_list = list(location_map.values())

        # Sort deterministically:
        # 1. Severity weight descending (Critical first)
        # 2. File path ascending
        # 3. Line number ascending
        # 4. Title ascending
        deduped_list.sort(
            key=lambda f: (
                -cls.SEVERITY_WEIGHT.get(f.severity, 0),
                f.file,
                f.line,
                f.title,
            )
        )

        return deduped_list
