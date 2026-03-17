"""Claude Code CLI adapter — POS tagging via `claude -p`.

Uses Claude Code's print mode (non-interactive). No API key needed —
authenticates via the user's existing Claude subscription.

Requires: Claude Code CLI installed (`npm install -g @anthropic-ai/claude-code`).
"""

from __future__ import annotations

import json
import shutil

from mhd_pos_benchmark.adapters.cli_base import CliLlmAdapter


class ClaudeCliAdapter(CliLlmAdapter):
    """POS tagger using Claude Code CLI in print mode."""

    # Map adapter model_name to Claude CLI --model flag
    _CLI_MODELS = {
        "claude-cli": "opus",
        "claude-cli-sonnet": "sonnet",
        "claude-cli-haiku": "haiku",
    }

    def __init__(
        self,
        model_name: str = "claude-cli",
        chunk_size: int = 200,
        cache_dir=None,
        max_retries: int = 3,
        timeout: int = 300,
        delay: float = 1.0,
    ) -> None:
        self._cli_model = self._CLI_MODELS.get(model_name, model_name)
        super().__init__(
            model_name=model_name,
            chunk_size=chunk_size,
            cache_dir=cache_dir,
            max_retries=max_retries,
            timeout=timeout,
            delay=delay,
        )

    def _build_command(self, system_prompt: str) -> list[str]:
        return [
            "claude", "-p",
            "--output-format", "json",
            "--model", self._cli_model,
            "--system-prompt", system_prompt,
        ]

    def _extract_text(self, stdout: str, stderr: str) -> str:
        data = json.loads(stdout)
        if "result" not in data:
            raise ValueError(f"No 'result' in Claude response: {list(data.keys())}")
        return data["result"]

    def _check_availability(self) -> tuple[bool, str]:
        if shutil.which("claude") is not None:
            return (True, "")
        return (
            False,
            "Claude Code CLI not found. "
            "Install: npm install -g @anthropic-ai/claude-code",
        )
