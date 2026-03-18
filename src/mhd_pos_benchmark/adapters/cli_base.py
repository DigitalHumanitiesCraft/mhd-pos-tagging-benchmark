"""Base class for CLI-subprocess-based LLM adapters.

Researchers with flat-rate LLM subscriptions (Claude Max, Google One AI Premium)
can use their CLI tools directly — no API keys or per-token billing needed.
This base class handles the chunk→call→retry→parse→cache pipeline; subclasses
only implement command building, response extraction, and availability checking.
"""

from __future__ import annotations

import logging
import subprocess
import time
from abc import abstractmethod
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


class CliLlmAdapter(ModelAdapter):
    """Base for adapters that call LLM CLI tools via subprocess."""

    def __init__(
        self,
        model_name: str,
        chunk_size: int = 200,
        cache_dir: Path | None = None,
        max_retries: int = 3,
        timeout: int = 120,
        delay: float = 1.0,
    ) -> None:
        self._model_name = model_name
        self._chunk_size = chunk_size
        self._max_retries = max_retries
        self._timeout = timeout
        self._delay = delay
        config_hash = ResultCache.make_config_hash(chunk_size, SYSTEM_PROMPT)
        self._cache = ResultCache(self.name, cache_dir, config_hash=config_hash)

        available, msg = self._check_availability()
        if not available:
            raise OSError(msg)

    @property
    def name(self) -> str:
        return self._model_name

    @abstractmethod
    def _build_command(self, system_prompt: str) -> list[str]:
        """Build the CLI command (without the user prompt, which goes to stdin)."""

    @abstractmethod
    def _extract_text(self, stdout: str, stderr: str) -> str:
        """Extract the LLM response text from subprocess output."""

    @abstractmethod
    def _check_availability(self) -> tuple[bool, str]:
        """Check if the CLI tool is installed. Returns (available, error_message)."""

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

            tags = self._call_cli(prompt, expected_count)
            all_tags.extend(tags)

            # Rate limiting between chunks
            if chunk_idx < len(chunks) - 1:
                time.sleep(self._delay)

        if len(all_tags) != len(forms):
            raise ValueError(
                f"Document {document.id}: expected {len(forms)} tags, got {len(all_tags)}"
            )

        self._cache.put(document.id, all_tags)
        return all_tags

    def _call_cli(self, user_prompt: str, expected_count: int) -> list[str]:
        """Call the CLI tool with retries and response validation."""
        cmd = self._build_command(SYSTEM_PROMPT)
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                result = subprocess.run(
                    cmd,
                    input=user_prompt,
                    capture_output=True,
                    encoding="utf-8",
                    timeout=self._timeout,
                )

                if result.returncode != 0:
                    raise RuntimeError(
                        f"CLI exited with code {result.returncode}: "
                        f"{result.stderr[:500]}"
                    )

                response_text = self._extract_text(result.stdout, result.stderr)
                tags = parse_tag_response(response_text, expected_count)
                return tags

            except subprocess.TimeoutExpired as e:
                last_error = e
                logger.warning(
                    "Attempt %d/%d timed out after %ds",
                    attempt, self._max_retries, self._timeout,
                )

            except (ValueError, RuntimeError) as e:
                last_error = e
                logger.warning(
                    "Attempt %d/%d failed: %s", attempt, self._max_retries, e,
                )

            if attempt < self._max_retries:
                time.sleep(2 ** attempt)

        raise RuntimeError(
            f"Failed after {self._max_retries} attempts: {last_error}"
        ) from last_error
