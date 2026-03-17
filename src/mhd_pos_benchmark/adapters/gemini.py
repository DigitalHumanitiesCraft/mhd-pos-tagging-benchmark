"""Gemini adapter — POS tagging via Google Gemini API.

API key resolution: --api-key flag > GEMINI_API_KEY env var.
Uses google-genai SDK (google-genai>=1.0).
"""

from __future__ import annotations

import json
import logging
import os
import time

from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.adapters.cache import ResultCache
from mhd_pos_benchmark.adapters.prompt_template import (
    SYSTEM_PROMPT,
    build_chunked_prompts,
    parse_tag_response,
)
from mhd_pos_benchmark.data.corpus import Document

logger = logging.getLogger(__name__)


class GeminiAdapter(ModelAdapter):
    """POS tagger using Google Gemini API."""

    def __init__(
        self,
        model: str = "gemini-3.1-pro",
        chunk_size: int = 200,
        cache_dir=None,
        temperature: float = 0.0,
        max_retries: int = 3,
        api_key: str | None = None,
    ) -> None:
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "No API key provided. Use --api-key or set GEMINI_API_KEY. "
                "Get a key at https://aistudio.google.com/apikey"
            )

        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._chunk_size = chunk_size
        self._temperature = temperature
        self._max_retries = max_retries
        config_hash = ResultCache.make_config_hash(chunk_size, SYSTEM_PROMPT)
        self._cache = ResultCache(f"gemini-{model}", cache_dir, config_hash=config_hash)

    @property
    def name(self) -> str:
        return f"gemini-{self._model}"

    def predict(self, document: Document) -> list[str]:
        mappable = document.mappable_tokens
        cached = self._cache.get(document.id, expected_count=len(mappable))
        if cached is not None:
            logger.info("Cache hit for %s", document.id)
            return cached
        forms = [t.form_diplomatic for t in mappable]

        if not forms:
            return []

        # Process in chunks
        all_tags: list[str] = []
        chunks = build_chunked_prompts(forms, chunk_size=self._chunk_size)

        for chunk_idx, (start, end, prompt) in enumerate(chunks):
            expected_count = end - start
            logger.info(
                "Document %s: chunk %d/%d (tokens %d–%d)",
                document.id, chunk_idx + 1, len(chunks), start, end,
            )

            tags = self._call_api(prompt, expected_count)
            all_tags.extend(tags)

        if len(all_tags) != len(forms):
            raise ValueError(
                f"Document {document.id}: expected {len(forms)} tags, got {len(all_tags)}"
            )

        # Cache the result
        self._cache.put(document.id, all_tags)
        return all_tags

    def _call_api(self, prompt: str, expected_count: int) -> list[str]:
        """Call Gemini API with retries and response validation."""
        from google.genai import types

        last_error = None
        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=self._temperature,
                        response_mime_type="application/json",
                    ),
                )

                if response.text is None:
                    raise ValueError("Gemini response blocked by safety filter")
                tags = parse_tag_response(response.text, expected_count)
                return tags

            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.warning(
                    "Attempt %d/%d failed: %s", attempt, self._max_retries, e
                )
                if attempt < self._max_retries:
                    time.sleep(2 ** attempt)

            except Exception as e:
                last_error = e
                logger.warning(
                    "API error attempt %d/%d: %s", attempt, self._max_retries, e
                )
                if attempt < self._max_retries:
                    time.sleep(2 ** attempt)

        raise RuntimeError(
            f"Failed after {self._max_retries} attempts: {last_error}"
        ) from last_error

