"""Google Gemini API client."""

from __future__ import annotations

import json
import re
from typing import Any

from src.config import Settings
from src.exceptions import GenerationError, LearningError
from src.logging_config import get_logger

logger = get_logger(__name__)


class GeminiClient:
    """Thin wrapper around the Gemini generative API."""

    def __init__(self, settings: Settings) -> None:
        if not settings.gemini_api_key:
            raise GenerationError(
                "GEMINI_API_KEY is not set. Add it to .env to use pattern extraction and drafting."
            )
        self._model_name = settings.gemini_model
        self._temperature = settings.gemini_temperature
        self._max_tokens = settings.gemini_max_tokens
        self._api_key = settings.gemini_api_key
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from google import genai
                from google.genai import types

                self._client = genai.Client(api_key=self._api_key)
                self._gen_config = types.GenerateContentConfig(
                    temperature=self._temperature,
                    max_output_tokens=self._max_tokens,
                )
            except Exception as exc:
                logger.exception("Failed to initialize Gemini client")
                raise GenerationError(f"Cannot initialize Gemini model '{self._model_name}'.") from exc
        return self._client

    def generate_text(self, prompt: str) -> str:
        try:
            client = self._get_client()
            response = client.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=self._gen_config,
            )
            text = response.text or ""
            if not text.strip():
                raise GenerationError("Gemini returned an empty response.")
            return text.strip()
        except GenerationError:
            raise
        except Exception as exc:
            logger.exception("Gemini generate_text failed")
            raise GenerationError("Gemini API call failed.") from exc

    def generate_json(self, prompt: str) -> dict[str, Any]:
        raw = self.generate_text(prompt)
        return _parse_json_response(raw)


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Extract JSON object from model output."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LearningError("Gemini returned invalid JSON for pattern extraction.") from exc
    raise LearningError("Gemini response did not contain parseable JSON.")