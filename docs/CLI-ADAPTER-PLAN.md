# Plan: CLI-Subscription Adapters for Flat-Rate LLM Users

## Context

Researchers with flat-rate LLM subscriptions (Claude Max ~$100-200/mo, Gemini Pro via Google One AI Premium) shouldn't need API keys and per-token billing to run the benchmark. They already have CLI tools installed (`claude`, `gemini`) that work with their subscriptions. This plan adds a subprocess-based adapter path alongside the existing API-based adapters.

**Key insight:** `claude -p "prompt"` runs non-interactively (print mode, outputs response, exits). No API key needed — uses the user's existing subscription auth.

## Architecture: Two-Layer Design

```
ModelAdapter (ABC)                      ← existing, unchanged
├── GoldPassthroughAdapter              ← existing
├── MajorityClassAdapter                ← existing
├── GeminiAdapter (API, needs key)      ← existing
└── CliLlmAdapter (new ABC)             ← subprocess-based base
    ├── ClaudeCliAdapter                ← claude -p
    └── GeminiCliAdapter                ← gemini (flags TBD)
```

**Why a shared `CliLlmAdapter` base?** The predict→chunk→call→retry→parse→cache pipeline is identical for all CLI tools. Only three things differ per tool: (1) how to build the command, (2) how to extract the LLM response from stdout, (3) how to check if the tool is installed.

## Files to Create/Modify

### NEW: `src/mhd_pos_benchmark/adapters/cli_base.py`

Shared base class for CLI-based adapters:

```python
class CliLlmAdapter(ModelAdapter):
    """Base for adapters that call LLM CLI tools via subprocess."""

    def __init__(self, model_name, chunk_size=200, cache_dir=None,
                 max_retries=3, timeout=120, delay=1.0): ...

    # Subclasses implement these three:
    @abstractmethod
    def _build_command(self, system_prompt: str, user_prompt: str) -> list[str]: ...
    @abstractmethod
    def _extract_text(self, stdout: str, stderr: str) -> str: ...
    @abstractmethod
    def _check_availability(self) -> tuple[bool, str]: ...

    # Base provides:
    def predict(self, document) -> list[str]:  # cache → chunk → call → assemble → cache
    def _call_cli(self, prompt, expected_count) -> list[str]:  # subprocess + retry
```

- Uses `subprocess.run(argv, capture_output=True, text=True, timeout=...)` — no `shell=True`, safe on Windows
- Reuses `build_chunked_prompts()` from `prompt_template.py`
- Reuses `ResultCache` from `cache.py`
- Rate limiting via configurable `delay` between calls (subscription plans have per-minute limits)

### NEW: `src/mhd_pos_benchmark/adapters/claude_cli.py`

Thin wrapper:

```python
class ClaudeCliAdapter(CliLlmAdapter):
    def _build_command(self, system_prompt, user_prompt):
        return ["claude", "-p", "--output-format", "json",
                "--system-prompt", system_prompt, user_prompt]

    def _extract_text(self, stdout, stderr):
        data = json.loads(stdout)
        return data["result"]  # unwrap Claude Code JSON envelope

    def _check_availability(self):
        return (bool(shutil.which("claude")),
                "Claude Code CLI not found. Install: npm install -g @anthropic-ai/claude-code")
```

### NEW: `src/mhd_pos_benchmark/adapters/gemini_cli.py`

Similar thin wrapper. **Open question:** Gemini CLI flags are less documented. May need `--json` or similar. Worst case: prepend system prompt to user prompt if no `--system-prompt` flag exists.

### REFACTOR: Extract `parse_tag_response()` as shared function

Currently duplicated logic in `GeminiAdapter._parse_response()`. Extract to `prompt_template.py`:

```python
def parse_tag_response(text: str, expected_count: int) -> list[str]:
    """Strip markdown fences, parse JSON array, validate MHDBDB tags."""
```

Used by: `GeminiAdapter`, `CliLlmAdapter`, future `ClaudeAdapter` (API).

### MODIFY: `src/mhd_pos_benchmark/cli.py`

- Add `"claude-cli"` and `"gemini-cli"` to `ADAPTER_CHOICES`
- Add to `_make_adapter()` with availability check at construction time
- Add optional `--chunk-size`, `--timeout`, `--delay` flags to `evaluate` and `compare`

### NEW: `tests/test_cli_adapters.py`

- Mock `subprocess.run` to test the full predict pipeline without real CLI tools
- Test retry on `TimeoutExpired`
- Test `_extract_text()` for Claude JSON envelope
- Test `_check_availability()` with mocked `shutil.which`
- Guard for optional integration test: `@pytest.mark.skipif(shutil.which("claude") is None)`

## Practical Concerns

| Concern | Mitigation |
|---------|-----------|
| System prompt is ~2000 chars | Well within argv limits (8191 on Windows). No temp file needed. |
| Rate limits on subscription plans | Configurable `--delay` (default 1s). Cache makes interrupted runs resumable. |
| Full corpus = ~10,500 chunks at 200 tokens | Subset mode (`--subset 10`) essential for prototyping. Full run is a long batch job. |
| Gemini CLI flags uncertain | Start with Claude (well-documented). Add Gemini CLI once we know the flags. |
| Cross-platform subprocess | `list[str]` argv (no `shell=True`) works on Windows + Unix. `shutil.which()` is cross-platform. |

## Verification

1. `pytest tests/` — all existing 23 tests still pass
2. `pytest tests/test_cli_adapters.py` — new mock-based tests pass
3. Manual: `mhd-bench evaluate ... --adapter claude-cli --subset 3 -v` (requires Claude Code installed)
4. Confirm caching: run twice, second run shows "Cache hit" in verbose output
5. `mhd-bench compare ... --adapters majority,claude-cli --subset 5` — side-by-side comparison works
