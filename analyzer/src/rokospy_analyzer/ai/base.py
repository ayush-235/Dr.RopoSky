"""Abstract Base Class for AI Intelligence Providers."""

import abc
from rokospy_analyzer.ai.models import AIContextData, AIFindingEnrichment


class AIProvider(abc.ABC):
    """Abstract interface for LLM enrichment providers (e.g. Gemini, future Claude)."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique identifier name for this AI provider."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Returns True if the required credentials and SDK/client are available."""
        pass

    @abc.abstractmethod
    def enrich_finding(self, context: AIContextData) -> AIFindingEnrichment:
        """
        Enriches a verified scanner finding with why_it_matters, impact, fix_steps,
        and before/after code examples.
        """
        pass
