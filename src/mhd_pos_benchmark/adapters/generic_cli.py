"""Generic CLI adapter — POS tagging via any LLM CLI tool.

Supports two modes:
1. **Preset mode** (recommended): `--preset claude`, `--preset gemini`, etc.
   Each preset knows how its CLI handles system prompts, output format, and flags.
2. **Custom mode** (fallback): `--cli-cmd "my-tool --flag"` for unknown CLIs.
   System prompt is embedded in the user prompt, output parsed as raw text.

Presets are defined in cli_presets.py (built-in) and optionally overridden
via cli-profiles.yaml in the repo root.

Calls run in an empty temporary directory unless the preset opts out. Agentic
CLIs pick up project instruction files from their working directory, which
would let the tagger read the benchmark's own documentation. See the
cli_presets module docstring for the measurements behind this.
"""

from __future__ import annotations

import logging
import re
import shlex
import shutil
import subprocess
import tempfile
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


def _npm_shim_launcher(executable_path: str) -> list[str] | None:
    """Turn an npm .CMD/.BAT wrapper into a direct `node <script>` invocation.

    On Windows, npm installs CLIs as batch wrappers. cmd.exe mangles a long
    multi-line argument passed through such a wrapper: measured 2026-08-18, the
    Copilot CLI received only the first line of the tagging prompt and answered
    nothing usable, while the same call through node returned correct tags.

    Only used for presets that pass the prompt as an argument; stdin delivery is
    unaffected. Returns None when the path is not an npm wrapper or the target
    script cannot be found, in which case the caller keeps the original path.
    """
    path = Path(executable_path)
    if path.suffix.lower() not in {".cmd", ".bat"}:
        return None

    node = shutil.which("node")
    if not node:
        return None

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None

    match = re.search(r'["\']?%~?dp0%?[\\/]?([^"\'\s%]*node_modules[^"\'\s%]*\.js)', content)
    if not match:
        return None

    script = (path.parent / match.group(1)).resolve()
    if not script.exists():
        return None

    logger.info("Bypassing npm wrapper %s, calling %s directly", path, script)
    return [node, str(script)]


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
        GenericCliAdapter(preset="claude", model="claude-opus-5")
        GenericCliAdapter(preset="gemini", model="gemini-3.1-pro-preview")

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
        timeout: int | None = None,
        delay: float = 1.0,
        isolate_cwd: bool | None = None,
    ) -> None:
        # Resolve preset or custom command
        if preset:
            self._preset = get_preset(preset)
            if self._preset is None:
                from mhd_pos_benchmark.adapters.cli_presets import list_presets

                available = ", ".join(sorted(list_presets()))
                raise ValueError(
                    f"Unknown CLI preset: '{preset}'. "
                    f"Available: {available}. "
                    f"Or use --cli-cmd for custom CLIs."
                )
            self._model = model or self._preset.default_model or "default"
            if self._preset.caveat:
                logger.warning("Preset '%s': %s", preset, self._preset.caveat)
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
        # Time per call scales with chunk size: a 1364-token chunk took 363 s
        # against Claude Opus 5, which the previous fixed 300 s would have
        # killed on every attempt. 300 s stays the floor for small chunks.
        self._timeout = timeout if timeout is not None else max(300, int(chunk_size * 0.8))
        self._delay = delay
        self._isolate_cwd = (
            self._preset.isolate_cwd if isolate_cwd is None else isolate_cwd
        )
        # Empty directory the CLI is invoked from, so it finds no project files.
        # Created lazily on first call and reused for the whole run.
        self._workdir: str | None = None

        # Resolve executable
        self._executable = self._preset.executable or shlex.split(self._preset.command)[0]
        from mhd_pos_benchmark.doctor import resolve_real_executable

        resolved = resolve_real_executable(self._executable)
        if not resolved:
            shadowed = shutil.which(self._executable)
            if shadowed:
                raise OSError(
                    f"Only an editor-bundled launcher was found for "
                    f"'{self._executable}' ({shadowed}). Install the real CLI; "
                    f"the launcher prompts interactively and cannot be scripted."
                )
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

        # Split first, substitute after: model names may contain spaces
        # (e.g. Antigravity's "Gemini 3.1 Pro (High)") and must stay one argument.
        cmd = [
            part.replace("{model}", self._model)
            for part in shlex.split(preset.command)
        ]

        # Resolve executable path. For argument-delivered prompts, bypass npm
        # batch wrappers, which truncate long multi-line arguments on Windows.
        if preset.prompt_delivery == "argument":
            launcher = _npm_shim_launcher(self._resolved_executable)
        else:
            launcher = None
        cmd[:1] = launcher or [self._resolved_executable]

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

    def _get_workdir(self) -> str | None:
        """Return the working directory for the subprocess, or None for the current one."""
        if not self._isolate_cwd:
            return None
        if self._workdir is None:
            self._workdir = tempfile.mkdtemp(prefix="mhd-bench-cli-")
            logger.debug("Isolated working directory: %s", self._workdir)
        return self._workdir

    def _call_cli(self, user_prompt: str, expected_count: int) -> list[str]:
        """Call the CLI tool with retries and response validation."""
        cmd, stdin_input = self._build_command(user_prompt)
        cwd = self._get_workdir()
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                result = subprocess.run(
                    cmd,
                    input=stdin_input,
                    capture_output=True,
                    encoding="utf-8",
                    timeout=self._timeout,
                    cwd=cwd,
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
