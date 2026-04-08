"""CLI presets — per-tool configuration for LLM CLI tools.

Each preset knows how its CLI handles:
- System prompt delivery (dedicated flag, embedded in user prompt, temp file)
- User prompt delivery (stdin, CLI argument)
- Output format and response extraction (raw text, JSON key, JSONL last event)
- Extra flags for non-interactive mode

Built-in presets: claude, gemini, codex, copilot.
User overrides: optional cli-profiles.yaml in repo root.
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


# ── Built-in presets ─────────────────────────────────────────────

BUILTIN_PRESETS: dict[str, CliPreset] = {
    "claude": CliPreset(
        name="claude",
        command="claude -p --output-format json --model {model}",
        system_prompt="flag",
        system_prompt_flag="--system-prompt",
        prompt_delivery="stdin",
        response_format="json_key",
        response_key="result",
        default_model="opus",
        executable="claude",
    ),
    "gemini": CliPreset(
        name="gemini",
        command="gemini --yolo -m {model} -p",
        system_prompt="embed",
        prompt_delivery="argument",
        response_format="raw",
        default_model="gemini-2.5-pro",
        executable="gemini",
    ),
    "codex": CliPreset(
        name="codex",
        command="codex exec --ephemeral --full-auto",
        system_prompt="embed",
        prompt_delivery="stdin",
        response_format="raw",
        default_model="gpt-4o",
        executable="codex",
    ),
    "copilot": CliPreset(
        name="copilot",
        command="copilot -p -s --no-ask-user --output-format text",
        system_prompt="embed",
        prompt_delivery="stdin",
        response_format="raw",
        default_model="gpt-4o",
        executable="copilot",
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
