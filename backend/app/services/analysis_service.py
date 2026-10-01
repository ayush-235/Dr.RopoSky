"""Analysis orchestration service — delegates to the Rokospy analyzer pipeline."""

import ipaddress
import logging
from typing import Any, Dict
from urllib.parse import urlparse

from rokospy_analyzer.config import config as analyzer_config
from rokospy_analyzer.pipeline import AnalyzerPipeline

logger = logging.getLogger(__name__)

_ALLOWED_GITHUB_HOSTS = {"github.com", "www.github.com"}


def _is_private_ip(hostname: str) -> bool:
    """Check if hostname resolves to a private/loopback IP."""
    try:
        addr = ipaddress.ip_address(hostname)
        return addr.is_private or addr.is_loopback or addr.is_reserved
    except ValueError:
        return False


def validate_github_url(url: str) -> str:
    """Validate and sanitize a GitHub repository URL.

    Raises ValueError if the URL is not a valid public GitHub repository URL.
    """
    if not url or not isinstance(url, str):
        raise ValueError("Repository URL is required")

    url = url.strip()

    parsed = urlparse(url)

    # Must be HTTPS
    if parsed.scheme not in ("https",):
        raise ValueError("Only HTTPS GitHub URLs are accepted")

    # No credentials in URL
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not accepted")

    # No port
    if parsed.port is not None:
        raise ValueError("URLs with explicit ports are not accepted")

    hostname = parsed.hostname or ""

    # Must be github.com
    if hostname.lower() not in _ALLOWED_GITHUB_HOSTS:
        raise ValueError("Only github.com repository URLs are accepted")

    # Reject private IPs (defense in depth)
    if _is_private_ip(hostname):
        raise ValueError("Private/internal addresses are not accepted")

    # Must have a path beyond just /
    path = parsed.path.strip("/")
    if not path or "/" not in path:
        raise ValueError("URL must point to a specific GitHub repository (owner/repo)")

    # Reconstruct clean URL (scheme + host + path only)
    clean_url = f"https://{hostname}/{path}"

    return clean_url


def _create_ai_provider():
    """Create a Gemini AI provider if API key is configured."""
    api_key = analyzer_config.GEMINI_API_KEY
    if not api_key:
        logger.info("GEMINI_API_KEY not configured — AI enrichment disabled")
        return None

    try:
        from rokospy_analyzer.ai.gemini_provider import GeminiProvider
        provider = GeminiProvider(
            api_key=api_key,
            model_name=analyzer_config.GEMINI_MODEL,
        )
        logger.info("Gemini AI provider initialized (model=%s)", analyzer_config.GEMINI_MODEL)
        return provider
    except Exception as e:
        logger.warning("Failed to initialize Gemini provider: %s — continuing without AI", e)
        return None


def run_analysis(target_input: str) -> Dict[str, Any]:
    """Execute the full Rokospy analysis pipeline and return the report as a dict.

    Args:
        target_input: GitHub URL or path to a ZIP file / local directory.

    Returns:
        Serialized AnalysisReport as a dictionary.

    Raises:
        RuntimeError: If analysis fails, with a sanitized error message.
    """
    try:
        ai_provider = _create_ai_provider()
        report = AnalyzerPipeline.analyze(target_input, ai_provider=ai_provider)
        return report.model_dump()
    except ValueError as e:
        # ValueError from pipeline validation (e.g., repo too large)
        raise RuntimeError(f"Analysis validation failed: {e}") from None
    except Exception as e:
        logger.error("Analysis pipeline error: %s", e, exc_info=True)
        raise RuntimeError("Analysis failed due to an internal error") from None
