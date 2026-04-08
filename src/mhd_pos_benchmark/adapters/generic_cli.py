"""Generic CLI adapter — POS tagging via any LLM CLI tool.

Supports two modes:
1. **Preset mode** (recommended): `--preset claude`, `--preset gemini`, etc.
   Each preset knows how its CLI handles system prompts, output format, and flags.
2. **Custom mode** (fallback): `--cli-cmd "my-tool --flag"` for unknown CLIs.
   System prompt is embedded in the user prompt, output parsed as raw text.

Presets are defined in cli_presets.py (built-in) and optionally overridden
via cli-profiles.yaml in the repo root.
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
from mhd_pos_benchmark.adapters.cli_presets import (
    CliPreset,
    extract_response,
    get_preset,
)
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


# Fallback preset for --cli-cmd mode (embed everything, stdin, raw output)
_CUSTOM_PRESET = CliPreset(
    name="custom",
    command="",  # filled from cli_cmd
    system_prompt="embed",
    prompt_delivery="stdin",
    response_format="raw",
)


class GenericCliAdapter(ModelAdapter):
    """POS tagger using any CLI tool, configured via presets or custom command.

    Preset mode (recommended):
        GenericCliAdapter(preset="claude", model="opus")
        GenericCliAdapter(preset="gemini", model="gemini-2.5-pro")

    Custom mode (fallback):
        GenericCliAdapter(cli_cmd="my-tool --flag", model_name="my-model")
    """

    def __init__(
        self,
        preset: str | None = None,
        cli_cmd: str | None = None,
        model: str | None = None,
        model_name: str | None = None,
        chunk_size: int = 200,
        cache_dir: Path | None = None,
        max_retries: int = 3,
        timeout: int = 300,
        delay: float = 1.0,
    ) -> None:
        # Resolve preset or custom command
        if preset:
            self._preset = get_preset(preset)
            if self._preset is None:
                available = ", ".join(
                    ["claude", "gemini", "codex", "copilot"]
                )
                raise ValueError(
                    f"Unknown CLI preset: '{preset}'. "
                    f"Available: {available}. "
                    f"Or use --cli-cmd for custom CLIs."
                )
            self._model = model or self._preset.default_model or "default"
        elif cli_cmd:
            self._preset = CliPreset(
                name="custom",
                command=cli_cmd,
                system_prompt="embed",
                prompt_delivery="stdin",
                response_format="raw",
            )
            self._model = model or model_name or f"cli-{shlex.split(cli_cmd)[0]}"
        else:
            raise ValueError("Either --preset or --cli-cmd is required")

        # model_name for display/cache (--model overrides)
        self._model_name = model_name or self._model
        self._chunk_size = chunk_size
        self._max_retries = max_retries
        self._timeout = timeout
        self._delay = delay

        # Resolve executable
        self._executable = self._preset.executable or shlex.split(self._preset.command)[0]
        resolved = shutil.which(self._executable)
        if not resolved:
            raise OSError(
                f"CLI tool '{self._executable}' not found on PATH. "
                f"Install it first."
            )
        self._resolved_executable = resolved

        config_hash = ResultCache.make_config_hash(chunk_size, SYSTEM_PROMPT)
        self._cache = ResultCache(self._model_name, cache_dir, config_hash=config_hash)

    @property
    def name(self) -> str:
        return self._model_name

    def _build_command(self, user_prompt: str) -> tuple[list[str], str | None]:
        """Build the subprocess command and optional stdin input.

        Returns (cmd_list, stdin_input_or_none).
        """
        preset = self._preset

        # Build the combined prompt (system + user) for embed mode
        if preset.system_prompt == "embed":
            full_prompt = _build_combined_prompt(SYSTEM_PROMPT, user_prompt)
        else:
            full_prompt = user_prompt

        # Build command from preset template (model substituted, prompt handled separately)
        cmd_str = preset.command.format(model=self._model)
        cmd = shlex.split(cmd_str)

        # Resolve executable path (Windows .cmd wrappers)
        cmd[0] = self._resolved_executable

        # Add system prompt flag if separate
        if preset.system_prompt == "flag" and preset.system_prompt_flag:
            cmd.extend([preset.system_prompt_flag, SYSTEM_PROMPT])

        # Add extra flags
        cmd.extend(preset.extra_flags)

        # Prompt delivery: stdin or appended as argument
        if preset.prompt_delivery == "argument":
            cmd.append(full_prompt)
            stdin = None
        else:
            stdin = full_prompt

        return cmd, stdin

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
        """Call the CLI tool with retries and response validation."""
        cmd, stdin_input = self._build_command(user_prompt)
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                result = subprocess.run(
                    cmd,
                    input=stdin_input,
                    capture_output=True,
                    encoding="utf-8",
                    timeout=self._timeout,
                )

                if result.returncode != 0:
                    raise RuntimeError(
                        f"CLI exited with code {result.returncode}: "
                        f"{result.stderr[:500]}"
                    )

                response_text = extract_response(result.stdout, self._preset)
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
                time.sleep(min(2 ** attempt, 60))

        raise RuntimeError(
            f"Failed after {self._max_retries} attempts: {last_error}"
        ) from last_error
