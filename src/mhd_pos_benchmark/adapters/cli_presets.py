"""CLI presets — per-tool configuration for LLM CLI tools.

Each preset knows how its CLI handles:
- System prompt delivery (dedicated flag, embedded in user prompt, temp file)
- User prompt delivery (stdin, CLI argument)
- Output format and response extraction (raw text, JSON key, JSONL last event)
- Extra flags for non-interactive mode
- Whether the call must run in an isolated working directory

Built-in presets: claude, gemini, antigravity, codex, copilot.
User overrides: optional cli-profiles.yaml in repo root.

## Why isolation matters

Modern coding CLIs are agentic harnesses, not bare model endpoints. Left alone
they load project instructions (CLAUDE.md, AGENTS.md, GEMINI.md), MCP servers,
skills, hooks and tool definitions into every request. For a benchmark that is
two separate defects:

1. **Contamination** — measured 2026-08-18: with the default invocation, a
   `claude -p` call started inside this repository could answer "which corpus
   and tagset does this project use?" correctly. The model under test was
   reading the benchmark's own documentation.
2. **Cost** — the same call carried 25.782 input tokens of harness overhead per
   chunk. With `--tools "" --strict-mcp-config` in an empty working directory
   it drops to 1.814, a factor of 14 on every single request.

Presets therefore carry isolation flags in the command template and set
`isolate_cwd`, which makes the adapter run the subprocess in an empty
temporary directory.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class CliPreset:
    """Configuration for a specific CLI tool."""

    # Display name
    name: str

    # Base command (without model — {model} is replaced at runtime)
    command: str

    # How system prompt is delivered: "flag", "embed", "file"
    system_prompt: str = "embed"

    # Flag name if system_prompt == "flag" (e.g. "--system-prompt")
    system_prompt_flag: str | None = None

    # How user prompt is delivered: "stdin", "argument"
    prompt_delivery: str = "stdin"

    # How to extract the response: "raw", "json_key", "jsonl_last"
    response_format: str = "raw"

    # JSON key to extract if response_format == "json_key"
    response_key: str | None = None

    # Extra flags always appended (e.g. --yolo for gemini)
    extra_flags: list[str] = field(default_factory=list)

    # Default model (used if --model not provided)
    default_model: str | None = None

    # CLI executable name (for availability check)
    executable: str | None = None

    # Run the subprocess in an empty temp dir instead of the current directory.
    # Keeps project instruction files (CLAUDE.md, AGENTS.md, ...) out of the prompt.
    isolate_cwd: bool = True

    # Shown by `mhd-bench doctor` and on adapter construction when set.
    caveat: str | None = None


# ── Built-in presets ─────────────────────────────────────────────

BUILTIN_PRESETS: dict[str, CliPreset] = {
    # Verified working 2026-08-18 against Claude Code 2.1.234.
    # --tools "" and --strict-mcp-config only take effect together: either flag
    # alone leaves the harness prompt at ~25k tokens (see module docstring).
    "claude": CliPreset(
        name="claude",
        command=(
            'claude -p --output-format json --model {model} '
            '--tools "" --strict-mcp-config --disable-slash-commands'
        ),
        system_prompt="flag",
        system_prompt_flag="--system-prompt",
        prompt_delivery="stdin",
        response_format="json_key",
        response_key="result",
        default_model="claude-opus-5",
        executable="claude",
    ),
    # Google retired the consumer tier of Gemini CLI on 2026-06-18: an OAuth
    # login now fails with IneligibleTierError. Only a paid GEMINI_API_KEY works.
    "gemini": CliPreset(
        name="gemini",
        command="gemini --yolo -m {model} -p",
        system_prompt="embed",
        prompt_delivery="argument",
        response_format="raw",
        default_model="gemini-3.1-pro-preview",
        executable="gemini",
        caveat=(
            "Gemini CLI no longer serves consumer accounts (retired 2026-06-18). "
            "Requires a paid GEMINI_API_KEY, otherwise use --adapter api "
            "--provider gemini."
        ),
    ),
    # Successor to Gemini CLI, on a Google account rather than an API key.
    # Model IDs are the left column of `agy models`, not the display names, and
    # reasoning depth is part of the ID. Full list read 2026-08-18:
    #   gemini-3.7-flash-{high,medium,low}, gemini-3.6-flash-{high,medium,low},
    #   gemini-3.5-flash-{high,medium,low}, gemini-3.1-pro-{high,low},
    #   claude-sonnet-4-6, claude-opus-4-6-thinking, gpt-oss-120b-medium
    # Note there is no gemini-3.1-pro-medium: Pro only ships high and low.
    # -p must come last with the prompt directly after it. Anywhere else (or via
    # stdin) agy silently ignores both the prompt and --model: it answered with a
    # greeting from its default model instead of the model that was requested.
    "antigravity": CliPreset(
        name="antigravity",
        command=(
            "agy --model {model} --disable-slash-commands "
            "--dangerously-skip-permissions --print-timeout 20m -p"
        ),
        system_prompt="embed",
        prompt_delivery="argument",
        response_format="raw",
        default_model="gemini-3.1-pro-high",
        executable="agy",
    ),
    # Verified working 2026-08-18 against codex-cli 0.147.0 on a ChatGPT plan
    # login (no API key needed). `codex exec -` reads the prompt from stdin and
    # prints the final message, and nothing else, to stdout.
    # --skip-git-repo-check is required because isolate_cwd runs the call in an
    # empty temp dir, which codex otherwise refuses as untrusted.
    # Authoritative model list: ~/.codex/models_cache.json, which the CLI refreshes
    # from the account. Read 2026-08-18 (client 0.147.0, ChatGPT plan), by priority:
    #   gpt-5.6-sol (1), gpt-5.6-terra (2), gpt-5.6-luna (3), gpt-5.5 (7),
    #   gpt-5.4 (16), gpt-5.4-mini (23), gpt-5.3-codex-spark (26)
    # Family names without a variant (gpt-5.6) and the older *-codex names do not
    # exist here and are rejected as "not supported when using Codex with a
    # ChatGPT account". Reasoning level is a separate setting, not part of the ID.
    "codex": CliPreset(
        name="codex",
        command="codex exec --ephemeral --skip-git-repo-check -m {model} -",
        system_prompt="embed",
        prompt_delivery="stdin",
        response_format="raw",
        default_model="gpt-5.6-sol",
        executable="codex",
    ),
    # Flags verified 2026-08-18 against GitHub Copilot CLI 1.0.80.
    # -p takes the prompt as an argument (not stdin), -s trims the stats block,
    # --no-custom-instructions keeps AGENTS.md and friends out of the prompt.
    "copilot": CliPreset(
        name="copilot",
        command=(
            "copilot --model {model} --no-ask-user --no-custom-instructions "
            "--log-level none --output-format text -s -p"
        ),
        system_prompt="embed",
        prompt_delivery="argument",
        response_format="raw",
        default_model="claude-sonnet-4.6",
        executable="copilot",
        caveat=(
            "Runs on a GitHub Copilot subscription. Never use --model auto for a "
            "published number: Copilot picks the model itself (it chose Claude "
            "Haiku 4.5 when tested). Accepted names, probed 2026-08-18 against "
            "CLI 1.0.80: claude-sonnet-4.6, claude-sonnet-4.5, claude-haiku-4.5, "
            "gpt-5.4, gpt-5.3-codex, gpt-5-mini, gemini-3.1-pro-preview, "
            "gemini-3.5-flash. Every claude-opus name was rejected."
        ),
    ),
}


def _load_yaml_profiles(yaml_path: Path | None = None) -> dict[str, CliPreset]:
    """Load user-defined CLI profiles from YAML, if it exists."""
    if yaml_path is None:
        yaml_path = Path("cli-profiles.yaml")
    if not yaml_path.exists():
        return {}

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        logger.warning("cli-profiles.yaml: expected dict at top level, got %s", type(data).__name__)
        return {}

    profiles: dict[str, CliPreset] = {}
    for name, config in data.items():
        if not isinstance(config, dict):
            logger.warning("cli-profiles.yaml: skipping '%s' (not a dict)", name)
            continue
        try:
            profiles[name] = CliPreset(
                name=name,
                command=config["command"],
                system_prompt=config.get("system_prompt", "embed"),
                system_prompt_flag=config.get("system_prompt_flag"),
                prompt_delivery=config.get("prompt_delivery", "stdin"),
                response_format=config.get("response_format", "raw"),
                response_key=config.get("response_key"),
                extra_flags=config.get("extra_flags", []),
                default_model=config.get("default_model"),
                executable=config.get("executable"),
                isolate_cwd=config.get("isolate_cwd", True),
                caveat=config.get("caveat"),
            )
        except KeyError as e:
            logger.warning("cli-profiles.yaml: '%s' missing required field %s", name, e)
    return profiles


def get_preset(name: str, yaml_path: Path | None = None) -> CliPreset | None:
    """Look up a CLI preset by name. User YAML overrides built-ins."""
    user_profiles = _load_yaml_profiles(yaml_path)
    return user_profiles.get(name) or BUILTIN_PRESETS.get(name)


def list_presets(yaml_path: Path | None = None) -> dict[str, CliPreset]:
    """Return all available presets (built-in + user YAML, user wins on conflict)."""
    merged = dict(BUILTIN_PRESETS)
    merged.update(_load_yaml_profiles(yaml_path))
    return merged


def extract_response(stdout: str, preset: CliPreset) -> str:
    """Extract the LLM response text from stdout based on preset config."""
    text = stdout.strip()
    if not text:
        raise ValueError("CLI returned empty stdout")

    if preset.response_format == "raw":
        return text

    elif preset.response_format == "json_key":
        if not preset.response_key:
            raise ValueError(f"Preset '{preset.name}' uses json_key but has no response_key")
        data = json.loads(text)
        if preset.response_key not in data:
            raise ValueError(
                f"No '{preset.response_key}' in CLI response: {list(data.keys())}"
            )
        return data[preset.response_key]

    elif preset.response_format == "jsonl_last":
        # Take the last non-empty line that parses as JSON
        for line in reversed(text.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # Look for content in common JSONL event formats
                if isinstance(data, dict):
                    for key in ("content", "text", "result", "message"):
                        if key in data:
                            return str(data[key])
                return line  # Return raw JSON line if no known key
            except json.JSONDecodeError:
                continue
        raise ValueError("No valid JSONL events in CLI output")

    else:
        raise ValueError(f"Unknown response_format: {preset.response_format}")
