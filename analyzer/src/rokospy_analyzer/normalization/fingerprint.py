"""Deterministic fingerprint generator for normalized findings."""

import hashlib


def generate_finding_fingerprint(scanner: str, rule_id: str, file_path: str, line: int, title: str = "") -> str:
    """
    Computes a deterministic SHA-256 fingerprint based on stable finding attributes.
    This guarantees consistent identification across re-scans and deduplication.
    """
    normalized_path = file_path.replace("\\", "/").strip("/")
    raw_key = f"{scanner.lower().strip()}:{rule_id.strip()}:{normalized_path}:{line}:{title.strip().lower()}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class FindingFingerprint:
    """Helper class providing a static/class interface for fingerprint generation."""

    @staticmethod
    def generate(scanner: str, rule_id: str, file_path: str, line: int, title: str = "") -> str:
        return generate_finding_fingerprint(scanner, rule_id, file_path, line, title)

