"""System diagnostics and corpus auto-detection.

Used by `mhd-bench doctor` and internally by CLI commands for corpus auto-detection.
All check functions return CheckResult dataclasses and have no side effects.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    """Result of a single diagnostic check."""

    name: str
    status: str  # "ok" | "warn" | "fail"
    message: str
    fix_hint: str = ""


# Corpus search paths, in priority order
_CORPUS_CANDIDATES = [
    "corpus",
    "ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml",
    "ReM-v2.1_coraxml/cora-xml",
    "cora-xml",
]

# CLI tools we know about: (binary_name, display_name, adapter_cmd_template, model_name)
_CLI_TOOLS = [
    ("claude", "Claude", 'claude -p --model opus', "claude-opus-4.6"),
    ("gemini", "Gemini", 'gemini -m gemini-2.5-pro -p', "gemini-2.5-pro"),
    ("codex", "Codex", 'codex exec', "codex"),
    ("copilot", "Copilot", 'copilot -p -s', "copilot"),
]

# API keys we look for: (env_var, provider_name, default_model)
_API_KEYS = [
    ("GEMINI_API_KEY", "gemini", "gemini-2.5-pro"),
    ("OPENAI_API_KEY", "openai", "gpt-4o"),
    ("MISTRAL_API_KEY", "mistral", "devstral"),
    ("GROQ_API_KEY", "groq", "llama-3.3-70b-versatile"),
]


def find_corpus_dir(base: Path | None = None) -> Path | None:
    """Search common locations for the ReM corpus directory.

    Returns the first directory containing at least one .xml file, or None.
    """
    base = base or Path(".")
    for candidate in _CORPUS_CANDIDATES:
        path = base / candidate
        if path.is_dir() and any(path.glob("*.xml")):
            return path
    return None


def check_python_version() -> CheckResult:
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 13):
        return CheckResult("Python", "ok", version_str)
    return CheckResult(
        "Python", "fail", version_str,
        fix_hint="Python 3.13+ required. Download from https://www.python.org/downloads/",
    )


def check_corpus(base: Path | None = None) -> CheckResult:
    path = find_corpus_dir(base)
    if path is not None:
        n_files = len(list(path.glob("*.xml")))
        return CheckResult("Corpus", "ok", f"{path} ({n_files} documents)")
    return CheckResult(
        "Corpus", "fail", "Not found",
        fix_hint="Download from https://www.linguistics.rub.de/rem/access/index.html\n"
                 "         Extract so that ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/*.xml exists",
    )


def check_openai_sdk() -> CheckResult:
    try:
        import openai  # noqa: F401
        return CheckResult("openai SDK", "ok", "installed")
    except ImportError:
        return CheckResult(
            "openai SDK", "warn", "not installed",
            fix_hint='pip install "mhd-pos-benchmark[api]"',
        )


def check_api_keys() -> list[CheckResult]:
    results = []
    for env_var, provider, _ in _API_KEYS:
        value = os.environ.get(env_var)
        if value:
            masked = value[:3] + "..." + value[-2:] if len(value) > 8 else "***"
            results.append(CheckResult(env_var, "ok", masked))
        else:
            results.append(CheckResult(env_var, "warn", "not set"))
    return results


def check_cli_tools() -> list[CheckResult]:
    results = []
    for binary, display, _, _ in _CLI_TOOLS:
        path = shutil.which(binary)
        if path:
            results.append(CheckResult(display, "ok", path))
        else:
            results.append(CheckResult(display, "warn", "not found"))
    return results


def check_cache_status(cache_dir: Path | None = None) -> list[CheckResult]:
    cache_dir = cache_dir or Path("results")
    results = []
    if cache_dir.exists():
        for model_dir in sorted(cache_dir.iterdir()):
            pred_file = model_dir / "predictions.jsonl"
            if model_dir.is_dir() and pred_file.exists():
                n_lines = sum(1 for line in pred_file.read_text(encoding="utf-8").splitlines() if line.strip())
                results.append(CheckResult(model_dir.name, "ok", f"{n_lines} documents cached"))
    return results


def suggest_commands(
    cli_results: list[CheckResult],
    api_key_results: list[CheckResult],
    cache_results: list[CheckResult],
    corpus_found: bool,
) -> list[str]:
    """Generate max 2 evaluate + 1 compare suggestion based on available tools.

    Priority:
    1. Max 1 CLI suggestion (flat-rate, cheapest) — first found CLI tool
    2. Max 1 API suggestion (fastest) — first found API key
    3. If >=2 cached models: compare command
    """
    if not corpus_found:
        return []

    suggestions: list[str] = []

    # 1. Best CLI option (first found)
    for (binary, display, cmd_template, model_name), result in zip(_CLI_TOOLS, cli_results):
        if result.status == "ok":
            suggestions.append(
                f'# Evaluate with {display} CLI (flat-rate, 3 documents):\n'
                f'mhd-bench evaluate --adapter cli --cli-cmd "{cmd_template}" '
                f'--model {model_name} --subset 3'
            )
            break

    # 2. Best API option (first found key)
    for (env_var, provider, default_model), result in zip(_API_KEYS, api_key_results):
        if result.status == "ok":
            suggestions.append(
                f'# Evaluate with {provider.title()} API (fast, 3 documents):\n'
                f'mhd-bench evaluate --adapter api --provider {provider} '
                f'--model {default_model} --subset 3'
            )
            break

    # 3. Compare cached results (if >=2 models)
    cached_models = [r.name for r in cache_results]
    if len(cached_models) >= 2:
        model_list = ",".join(cached_models[:4])  # cap at 4 for readability
        suggestions.append(
            f'# Compare your cached results:\n'
            f'mhd-bench compare --models {model_list}'
        )

    # 4. Nothing found at all
    if not suggestions:
        is_windows = sys.platform == "win32"
        export_cmd = "set GEMINI_API_KEY=your-key-here" if is_windows else "export GEMINI_API_KEY=your-key-here"
        suggestions.append(
            'No taggers detected. Quickest way to start:\n'
            '  1. Get a free Gemini API key: https://aistudio.google.com/apikey\n'
            '  2. pip install "mhd-pos-benchmark[api]"\n'
            f'  3. {export_cmd}\n'
            '  4. mhd-bench evaluate --adapter api --provider gemini --subset 3'
        )

    return suggestions


def run_all_checks(base: Path | None = None) -> dict:
    """Run all diagnostic checks. Returns dict with all results."""
    return {
        "python": check_python_version(),
        "corpus": check_corpus(base),
        "openai_sdk": check_openai_sdk(),
        "api_keys": check_api_keys(),
        "cli_tools": check_cli_tools(),
        "cache": check_cache_status(),
    }
