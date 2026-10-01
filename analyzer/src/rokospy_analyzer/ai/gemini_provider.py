"""Google Gemini implementation of the AIProvider interface."""

import os
from typing import Optional
from rokospy_analyzer.ai.base import AIProvider
from rokospy_analyzer.ai.models import (
    AIContextData,
    AIFindingEnrichment,
    AIConfidenceEnum,
    AIStatusEnum,
)
from rokospy_analyzer.ai.prompts import AIPromptBuilder
from rokospy_analyzer.ai.validator import AIResponseValidator
from rokospy_analyzer.config import config


class GeminiProvider(AIProvider):
    """Google Gemini AI Provider utilizing the official Google GenAI SDK."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self._api_key = api_key or config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        self._model_name = model_name or config.GEMINI_MODEL or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._client = None

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    def is_available(self) -> bool:
        """Returns True if a Gemini API key is configured."""
        return bool(self._api_key and self._api_key.strip())

    def _get_client(self):
        """Lazy client instantiation."""
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Google GenAI client: {str(e)}") from e
        return self._client

    def enrich_finding(self, context: AIContextData) -> AIFindingEnrichment:
        """Calls Gemini API with sanitized context to generate educational remediation."""
        if not self.is_available():
            return AIFindingEnrichment(
                why_it_matters="AI explanation unavailable (GEMINI_API_KEY is not configured).",
                impact="Analysis proceeded with tool-confirmed scanner evidence.",
                fix_steps=["Refer to the scanner rule documentation to remediate this finding."],
                code_before=context.evidence,
                code_after="",
                confidence=AIConfidenceEnum.LOW,
                status=AIStatusEnum.UNAVAILABLE,
                error_message="GEMINI_API_KEY is not configured",
            )

        user_prompt = AIPromptBuilder.build_user_prompt(context)

        try:
            client = self._get_client()
            
            # Configure structured generation
            response = client.models.generate_content(
                model=self._model_name,
                contents=user_prompt,
                config={
                    "system_instruction": AIPromptBuilder.SYSTEM_INSTRUCTION,
                    "response_mime_type": "application/json",
                },
            )

            raw_text = getattr(response, "text", "") or ""
            enrichment, err = AIResponseValidator.validate_and_parse(raw_text)

            if err or not enrichment:
                return AIFindingEnrichment(
                    why_it_matters=f"Issue detected by {context.scanner} (Rule: {context.rule_id}).",
                    impact="AI response validation failed.",
                    fix_steps=["Review scanner message and inspect code location directly."],
                    code_before=context.evidence,
                    code_after="",
                    confidence=AIConfidenceEnum.LOW,
                    status=AIStatusEnum.FAILED,
                    error_message=err or "Invalid response schema",
                )

            return enrichment

        except Exception as e:
            err_msg = str(e)
            return AIFindingEnrichment(
                why_it_matters=f"Issue detected by {context.scanner} (Rule: {context.rule_id}).",
                impact="AI explanation could not be generated due to provider error.",
                fix_steps=["Review scanner message and inspect code location directly."],
                code_before=context.evidence,
                code_after="",
                confidence=AIConfidenceEnum.LOW,
                status=AIStatusEnum.FAILED,
                error_message=f"Gemini API error: {err_msg}",
            )
