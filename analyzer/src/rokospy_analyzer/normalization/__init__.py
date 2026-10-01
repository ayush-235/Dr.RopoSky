"""Normalization package exports."""

from rokospy_analyzer.normalization.fingerprint import generate_finding_fingerprint
from rokospy_analyzer.normalization.deduplicator import FindingDeduplicator

__all__ = ["generate_finding_fingerprint", "FindingDeduplicator"]
