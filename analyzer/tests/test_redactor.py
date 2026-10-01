"""Tests for SecretRedactor ensuring zero secret leakage."""

import pytest
from rokospy_analyzer.security.redactor import SecretRedactor


def test_redact_aws_keys():
    fake_key = "AKIAIOSFODNN7EXAMPLE"
    code_line = f'AWS_ACCESS_KEY_ID = "{fake_key}"'
    redacted = SecretRedactor.redact(code_line)
    assert fake_key not in redacted
    assert "[REDACTED_SECRET]" in redacted


def test_redact_github_tokens():
    fake_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    code_line = f'const token = "{fake_token}";'
    redacted = SecretRedactor.redact(code_line)
    assert fake_token not in redacted
    assert "[REDACTED_SECRET]" in redacted


def test_redact_stripe_keys():
    # Synthetic test-only fixture to verify redaction regex without triggering secret scanning
    fake_stripe = "sk_test_" + "FakeStripeKeyForTestingOnly00000000"
    code_line = f'stripe = Stripe("{fake_stripe}")'
    redacted = SecretRedactor.redact(code_line)
    assert fake_stripe not in redacted
    assert "[REDACTED_SECRET]" in redacted


def test_redact_jwt_tokens():
    fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgN_fake_signature_hash123"
    text = f"Bearer {fake_jwt}"
    redacted = SecretRedactor.redact(text)
    assert fake_jwt not in redacted
    assert "[REDACTED_SECRET]" in redacted


def test_redact_generic_passwords():
    code_line = 'password = "SuperSecretPassword123!"'
    redacted = SecretRedactor.redact(code_line)
    assert "SuperSecretPassword123!" not in redacted
    assert "[REDACTED_SECRET]" in redacted


def test_contains_secret_detection():
    assert SecretRedactor.contains_secret('API_KEY = "AKIAIOSFODNN7EXAMPLE"') is True
    assert SecretRedactor.contains_secret('x = 1 + 2') is False
    assert SecretRedactor.contains_secret('const api = "YOUR_API_KEY"') is False  # Placeholder ignored
