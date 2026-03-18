"""Generic CLI adapter — POS tagging via any LLM CLI tool.

Works with any CLI that accepts a prompt and returns text:
  - Gemini CLI:  gemini -m gemini-2.5-flash -p
  - Codex CLI:   codex exec
  - Copilot CLI: copilot -p -s
  - Vibe CLI:    vibe --prompt
  - Any other:   mycli --flag

Since most CLIs don't support inline system prompts, the system prompt
is embedded into the user prompt. The prompt is sent via stdin (avoids
argument-length limits and shell-escaping issues on Windows). CLIs that
need a prompt flag (like `-p`) should use `-p ""` — stdin is appended.
"""

from __future__ import annotations

import logging
import shlex
import shutil
import subprocess
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


def _build_combined_prompt(system_prompt: str, user_prompt: str) -> str:
    """Embed system prompt into user prompt for CLIs without system prompt support.

    Task-first structure: the immediate task comes first so agentic CLIs
    (Gemini, Codex, Copilot) execute it instead of treating the prompt
    as session setup. The system prompt follows as reference material.
    """
    return (
        f"{user_prompt}\n\n"
        f"--- REFERENCE ---\n"
        f"{system_prompt}"
    )


class GenericCliAdapter(ModelAdapter):
    """POS tagger using any CLI tool that accepts a prompt argument.

    The prompt is passed as the final positional argument to the CLI command.
    Response is read from stdout and parsed for a JSON tag array.

    Examples:
        GenericCliAdapter("gemini -p")           # Gemini CLI
        GenericCliAdapter("codex exec")           # OpenAI Codex CLI
        GenericCliAdapter("copilot -p -s")        # GitHub Copilot CLI
        GenericCliAdapter("vibe --prompt")         # Mistral Vibe CLI
    """

    def __init__(
        self,
        cli_cmd: str,
        model_name: str | None = None,
        chunk_size: int = 200,
        cache_dir: Path | None = None,
        max_retries: int = 3,
        timeout: int = 300,
        delay: float = 1.0,
    ) -> None:
        self._cli_parts = shlex.split(cli_cmd)
        if not self._cli_parts:
            raise ValueError("--cli-cmd must not be empty")

        self._executable = self._cli_parts[0]
        # Resolve full path (needed on Windows for npm-installed .cmd wrappers)
        resolved = shutil.which(self._executable)
        if resolved:
            self._cli_parts[0] = resolved
        self._model_name = model_name or f"cli-{self._executable}"
        self._chunk_size = chunk_size
        self._max_retries = max_retries
        self._timeout = timeout
        self._delay = delay

        available, msg = self._check_availability()
        if not available:
            raise OSError(msg)

        config_hash = ResultCache.make_config_hash(chunk_size, SYSTEM_PROMPT)
        self._cache = ResultCache(self._model_name, cache_dir, config_hash=config_hash)

    @property
    def name(self) -> str:
        return self._model_name

    def _check_availability(self) -> tuple[bool, str]:
        if shutil.which(self._executable) is not None:
            return (True, "")
        return (
            False,
            f"CLI tool '{self._executable}' not found on PATH. "
            f"Install it or check your --cli-cmd.",
        )

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

        for chunk_idx, (start, end, user_prompt) in enumerate(chunks):
            expected_count = end - start
            logger.info(
                "Document %s: chunk %d/%d (tokens %d-%d)",
                document.id, chunk_idx + 1, len(chunks), start, end,
            )

            tags = self._call_cli(user_prompt, expected_count)
            all_tags.extend(tags)

            if chunk_idx < len(chunks) - 1:
                time.sleep(self._delay)

        if len(all_tags) != len(forms):
            raise ValueError(
                f"Document {document.id}: expected {len(forms)} tags, got {len(all_tags)}"
            )

        self._cache.put(document.id, all_tags)
        return all_tags

    def _call_cli(self, user_prompt: str, expected_count: int) -> list[str]:
        """Call the CLI tool with the combined prompt via stdin.

        Prompt is sent via stdin rather than as a CLI argument to avoid
        argument-length limits (Windows: ~8191 chars) and shell-escaping issues.
        If the command ends with a prompt flag (e.g. -p, --prompt), an empty
        string is appended so the flag gets a value and stdin provides the content.
        """
        combined = _build_combined_prompt(SYSTEM_PROMPT, user_prompt)
        cmd = list(self._cli_parts)
        # If the last arg is a prompt flag, it needs a value — use empty string
        # so the real content comes from stdin
        if cmd[-1] in ("-p", "--prompt"):
            cmd.append("")
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                result = subprocess.run(
                    cmd,
                    input=combined,
                    capture_output=True,
                    encoding="utf-8",
                    timeout=self._timeout,
                )

                if result.returncode != 0:
                    raise RuntimeError(
                        f"CLI exited with code {result.returncode}: "
                        f"{result.stderr[:500]}"
                    )

                response_text = result.stdout.strip()
                if not response_text:
                    raise ValueError("CLI returned empty stdout")

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
