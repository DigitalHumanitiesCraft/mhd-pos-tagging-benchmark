"""Generic API adapter — POS tagging via any OpenAI-compatible LLM API.

Works with any provider that offers an OpenAI-compatible chat completions endpoint:
  - OpenAI:  gpt-4o, o3, ...
  - Gemini:  gemini-2.5-pro, gemini-2.5-flash, ...
  - Mistral: devstral, mistral-large, ...
  - Groq:    llama3, mixtral, ...
  - Local:   ollama, vLLM, llama.cpp, ...

One SDK (openai), one adapter. Just needs --provider, --model, --api-key.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.adapters.cache import ResultCache
from mhd_pos_benchmark.adapters.prompt_template import (
    SYSTEM_PROMPT,
    build_chunked_prompts,
    parse_tag_response,
)
from mhd_pos_benchmark.data.corpus import Document

logger = logging.getLogger(__name__)

# Known providers with their base URLs and env var names for API keys.
# Users can also pass --api-base directly for unlisted providers.
PROVIDERS: dict[str, dict[str, str]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "env_var": "OPENAI_API_KEY",
        "default_model": "gpt-4o",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "env_var": "GEMINI_API_KEY",
        "default_model": "gemini-2.5-flash",
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "env_var": "MISTRAL_API_KEY",
        "default_model": "mistral-large-latest",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env_var": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
}


class GenericApiAdapter(ModelAdapter):
    """POS tagger using any OpenAI-compatible LLM API.

    Uses the openai SDK to talk to any provider. Provider presets handle
    base URLs and env var names; --api-base overrides for custom endpoints.

    Examples:
        GenericApiAdapter(provider="openai", model="gpt-4o", api_key="sk-...")
        GenericApiAdapter(provider="gemini", model="gemini-2.5-pro", api_key="AI...")
        GenericApiAdapter(provider="mistral", model="devstral", api_key="...")
        GenericApiAdapter(api_base="http://localhost:11434/v1", model="llama3")
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
        chunk_size: int = 200,
        cache_dir: Path | None = None,
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> None:
        # Resolve provider config
        provider_config = PROVIDERS.get(provider, {})
        self._base_url = api_base or provider_config.get("base_url", "https://api.openai.com/v1")
        self._model = model or provider_config.get("default_model", "gpt-4o")

        # Resolve API key: explicit > env var > error
        env_var = provider_config.get("env_var", "OPENAI_API_KEY")
        api_key = api_key or os.environ.get(env_var)
        if not api_key:
            # For local endpoints (ollama etc.) an API key may not be needed
            if "localhost" in self._base_url or "127.0.0.1" in self._base_url:
                api_key = "not-needed"
            else:
                raise OSError(
                    f"No API key provided. Use --api-key or set {env_var}."
                )

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "The 'openai' package is required for --adapter api. "
                "Install with: pip install mhd-pos-benchmark[api]"
            ) from None

        self._client = OpenAI(api_key=api_key, base_url=self._base_url)
        self._chunk_size = chunk_size
        self._temperature = temperature
        self._max_retries = max_retries
        config_hash = ResultCache.make_config_hash(chunk_size, SYSTEM_PROMPT, temperature=temperature)
        self._cache = ResultCache(self.name, cache_dir, config_hash=config_hash)

    @property
    def name(self) -> str:
        return self._model

    def predict(self, document: Document) -> list[str]:
        mappable = document.mappable_tokens
        cached = self._cache.get(document.id, expected_count=len(mappable))
        if cached is not None:
            logger.info("Cache hit for %s", document.id)
            return cached
        forms = [t.form_for_tagging for t in mappable]

        if not forms:
            return []

        all_tags: list[str] = []
        chunks = build_chunked_prompts(forms, chunk_size=self._chunk_size)

        for chunk_idx, (start, end, prompt) in enumerate(chunks):
            expected_count = end - start
            logger.info(
                "Document %s: chunk %d/%d (tokens %d-%d)",
                document.id, chunk_idx + 1, len(chunks), start, end,
            )

            tags = self._call_api(prompt, expected_count)
            all_tags.extend(tags)

        if len(all_tags) != len(forms):
            raise ValueError(
                f"Document {document.id}: expected {len(forms)} tags, got {len(all_tags)}"
            )

        self._cache.put(document.id, all_tags)
        return all_tags

    def _call_api(self, prompt: str, expected_count: int) -> list[str]:
        """Call the API with retries and response validation."""
        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self._temperature,
                )

                text = response.choices[0].message.content
                if text is None:
                    raise ValueError("API response has no content (possibly filtered)")
                tags = parse_tag_response(text, expected_count)
                return tags

            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.warning(
                    "Attempt %d/%d failed: %s", attempt, self._max_retries, e
                )
                if attempt < self._max_retries:
                    time.sleep(min(2 ** attempt, 60))

            except OSError as e:
                last_error = e
                logger.warning(
                    "API error attempt %d/%d: %s", attempt, self._max_retries, e
                )
                if attempt < self._max_retries:
                    time.sleep(min(2 ** attempt, 60))

        raise RuntimeError(
            f"Failed after {self._max_retries} attempts: {last_error}"
        ) from last_error
