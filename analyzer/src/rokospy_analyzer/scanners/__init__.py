"""Scanners package and registry."""

from typing import List
from rokospy_analyzer.scanners.base import BaseScanner
from rokospy_analyzer.scanners.secret_scanner import BuiltinSecretScanner
from rokospy_analyzer.scanners.essentials_scanner import ProjectEssentialsScanner
from rokospy_analyzer.scanners.intelligence_scanner import ProjectIntelligenceScanner
from rokospy_analyzer.scanners.gitleaks_scanner import GitleaksScanner
from rokospy_analyzer.scanners.bandit_scanner import BanditScanner
from rokospy_analyzer.scanners.ruff_scanner import RuffScanner
from rokospy_analyzer.scanners.semgrep_scanner import SemgrepScanner
from rokospy_analyzer.scanners.eslint_scanner import ESLintScanner
from rokospy_analyzer.scanners.npm_audit_scanner import NpmAuditScanner
from rokospy_analyzer.scanners.pip_audit_scanner import PipAuditScanner


def get_all_scanners() -> List[BaseScanner]:
    """Returns an ordered list of all registered scanner instances."""
    return [
        # 1. Built-in Security & Essentials & Intelligence
        BuiltinSecretScanner(),
        ProjectEssentialsScanner(),
        ProjectIntelligenceScanner(),

        # 2. Dedicated Secret Scanner
        GitleaksScanner(),

        # 3. Multi-language SAST
        SemgrepScanner(),

        # 4. Python Analyzers
        BanditScanner(),
        RuffScanner(),
        PipAuditScanner(),

        # 5. JavaScript / TypeScript Analyzers
        ESLintScanner(),
        NpmAuditScanner(),
    ]


__all__ = [
    "BaseScanner",
    "BuiltinSecretScanner",
    "ProjectEssentialsScanner",
    "ProjectIntelligenceScanner",
    "GitleaksScanner",
    "SemgrepScanner",
    "BanditScanner",
    "RuffScanner",
    "ESLintScanner",
    "NpmAuditScanner",
    "PipAuditScanner",
    "get_all_scanners",
]

