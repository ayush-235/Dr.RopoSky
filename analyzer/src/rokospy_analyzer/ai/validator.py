"""Response validation and normalization for AI enrichment outputs."""

import json
import re
from typing import Optional, Tuple
from rokospy_analyzer.ai.models import AIFindingEnrichment, AIConfidenceEnum, AIStatusEnum


class AIValidationError(Exception):
    """Raised when an AI response fails validation or JSON parsing."""
    pass


class AIResponseValidator:
    """Extracts, cleans, and validates structured JSON responses from LLM providers."""

    @classmethod
    def clean_json_string(cls, raw_text: str) -> str:
        """Strips markdown code fences and extraneous whitespace."""
        text = raw_text.strip()
        # Remove ```json ... ``` or ``` ... ```
        if text.startswith("```"):
            # Match first ```[a-zA-Z]* and last ```
            match = re.search(r"^```(?:json)?\s*([\s\S]*?)\s*```$", text, re.IGNORECASE)
            if match:
                text = match.group(1).strip()
            else:
                # Strip leading ``` line and trailing ```
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
        return text

    @classmethod
    def validate_and_parse(cls, raw_text: str) -> Tuple[Optional[AIFindingEnrichment], Optional[str]]:
        """
        Parses raw text into AIFindingEnrichment.
        Returns (enrichment, error_message).
        """
        if not raw_text or not raw_text.strip():
            return None, "Empty response from AI provider"

        cleaned = cls.clean_json_string(raw_text)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            # Fallback regex extraction if model included surrounding text
            json_match = re.search(r"\{[\s\S]*\}", cleaned)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    return None, f"Malformed JSON from AI provider: {str(e)}"
            else:
                return None, f"Failed to parse AI response as JSON: {str(e)}"

        if not isinstance(data, dict):
            return None, "AI response JSON must be a dictionary object"

        # Normalize confidence
        raw_conf = str(data.get("confidence", "high")).lower().strip()
        conf = AIConfidenceEnum.HIGH
        if "med" in raw_conf:
            conf = AIConfidenceEnum.MEDIUM
        elif "low" in raw_conf:
            conf = AIConfidenceEnum.LOW

        # Ensure fix_steps is a list
        fix_steps = data.get("fix_steps", [])
        if isinstance(fix_steps, str):
            fix_steps = [fix_steps]
        elif not isinstance(fix_steps, list):
            fix_steps = [str(fix_steps)]

        try:
            enrichment = AIFindingEnrichment(
                why_it_matters=str(data.get("why_it_matters", "No explanation provided.")),
                impact=str(data.get("impact", "")),
                fix_steps=[str(step) for step in fix_steps],
                code_before=str(data.get("code_before", "")),
                code_after=str(data.get("code_after", "")),
                confidence=conf,
                status=AIStatusEnum.SUCCESS,
                error_message=None,
            )
            return enrichment, None
        except Exception as e:
            return None, f"Schema validation failed: {str(e)}"
