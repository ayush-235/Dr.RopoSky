"""Secret Redaction Engine for Rokospy.

Guarantees that raw credentials, tokens, and keys are NEVER exposed in logs, reports,
UI displays, or LLM prompt payloads.
"""

import re
from typing import Optional, List, Pattern
from rokospy_analyzer.config import config


class SecretRedactor:
    """Detects and redacts secret tokens, API keys, passwords, and private keys."""

    PATTERNS: List[tuple[str, Pattern[str]]] = [
        # AWS Keys
        ("AWS Access Key", re.compile(r"\b(AKIA[0-9A-Z]{16})\b")),
        ("AWS Secret Key Assignment", re.compile(r"""(?i)(?:aws_secret_access_key|aws_secret_key|secret_key)\s*[:=]\s*['"]?([A-Za-z0-9/+=]{40})['"]?""")),

        # GitHub Tokens
        ("GitHub Personal Access Token", re.compile(r"\b(ghp_[a-zA-Z0-9]{36})\b")),
        ("GitHub OAuth Token", re.compile(r"\b(gho_[a-zA-Z0-9]{36})\b")),
        ("GitHub User-to-Server Token", re.compile(r"\b(ghu_[a-zA-Z0-9]{36})\b")),
        ("GitHub Server-to-Server Token", re.compile(r"\b(ghs_[a-zA-Z0-9]{36})\b")),
        ("GitHub Refresh Token", re.compile(r"\b(ghr_[a-zA-Z0-9]{36})\b")),
        ("GitHub Fine-grained PAT", re.compile(r"\b(github_pat_[a-zA-Z0-9_]{82})\b")),

        # Stripe Keys
        ("Stripe Secret Key", re.compile(r"\b(sk_(?:live|test)_[0-9a-zA-Z]{24,99})\b")),
        ("Stripe Restricted Key", re.compile(r"\b(rk_(?:live|test)_[0-9a-zA-Z]{24,99})\b")),

        # Slack Tokens
        ("Slack Token", re.compile(r"\b(xox[baprs]-[0-9a-zA-Z]{10,48})\b")),

        # Generic Private Keys
        ("Private Key Block", re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH|DSA|PGP|ENCRYPTED)? ?PRIVATE KEY-----[\s\S]*?-----END (?:RSA|EC|OPENSSH|DSA|PGP|ENCRYPTED)? ?PRIVATE KEY-----")),

        # JSON Web Tokens (JWT)
        ("JSON Web Token", re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b")),

        # Generic Secret / Key assignments in code
        (
            "Generic Secret Assignment",
            re.compile(
                r"""(?i)(?:api_key|apikey|secret|password|passwd|auth_token|access_token|client_secret|private_key)\s*[:=]\s*['"]([^'"\r\n\s]{8,})['"]"""
            ),
        ),

        # Authorization Header
        (
            "Authorization Header",
            re.compile(r"""(?i)(?:bearer\s+[a-zA-Z0-9._~+/-]{15,})"""),
        ),
    ]

    @classmethod
    def redact(cls, text: Optional[str]) -> str:
        """Redacts all detected sensitive secrets from the provided text."""
        if not text:
            return ""

        redacted = text
        for label, pattern in cls.PATTERNS:
            def _replace_match(match: re.Match) -> str:
                # If group 1 exists, replace group 1 value while preserving context
                if match.groups() and match.group(1):
                    full_span = match.group(0)
                    g1_val = match.group(1)
                    # Skip common placeholder keywords
                    if g1_val.upper() in {"YOUR_API_KEY", "CHANGE_ME", "EXAMPLE", "REDACTED", "PLACEHOLDER", "TEST_KEY"}:
                        return full_span
                    return full_span.replace(g1_val, config.REDACTION_STRING)
                return config.REDACTION_STRING

            redacted = pattern.sub(_replace_match, redacted)

        return redacted

    @classmethod
    def contains_secret(cls, text: Optional[str]) -> bool:
        """Returns True if the text matches any known secret pattern."""
        if not text:
            return False
        for _, pattern in cls.PATTERNS:
            match = pattern.search(text)
            if match:
                # Filter out obvious template placeholders
                val = match.group(1) if match.groups() and match.group(1) else match.group(0)
                if val.upper() not in {"YOUR_API_KEY", "CHANGE_ME", "EXAMPLE", "REDACTED", "PLACEHOLDER", "TEST_KEY"}:
                    return True
        return False
