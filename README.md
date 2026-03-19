# MHD POS Tagging Benchmark

Model-agnostic benchmark for Part-of-Speech tagging of Middle High German texts against [ReM](https://www.linguistics.rub.de/rem/) ground truth. Evaluates any POS tagger (LLM, encoder, classical) via a pluggable adapter interface.

**New here?** Start with `mhd-bench doctor` — it checks your setup and tells you exactly what to do next.

## Quick Start

```bash
pip install -e ".[dev]"

# Download ReM corpus (106 MB) from https://www.linguistics.rub.de/rem/access/index.html
# Extract into repo root (corpus is auto-detected)

mhd-bench doctor                                     # check setup, get suggestions
mhd-bench evaluate --adapter passthrough --subset 3   # sanity check (100% accuracy)
```

## Evaluate a Model

```bash
# Via CLI tool (Claude, Gemini CLI, Codex, Copilot, ...)
mhd-bench evaluate --adapter cli \
  --cli-cmd "claude -p --model opus" --model claude-opus-4.6 --subset 3

# Via API (OpenAI, Gemini, Mistral, Groq, Ollama, ...)
mhd-bench evaluate --adapter api \
  --provider gemini --model gemini-2.5-pro --api-key --subset 3

# Via custom adapter (BERT, CRF, HMM, ...)
# See docs/guides/MODEL-ADAPTER-GUIDE.md
```

Results are cached in `results/<model>/predictions.jsonl` and reused automatically.

## Compare Models

```bash
# Compare cached results from previous evaluate runs — instant, no API calls
mhd-bench compare --models claude-opus-4.6,gemini-2.5-pro --subset 3

# Compare baselines live
mhd-bench compare --adapters passthrough,majority --subset 3
```

## CLI Reference

```bash
mhd-bench doctor                                       # check setup, suggest commands
mhd-bench parse [corpus_dir] [--stats]                 # parse corpus (auto-detected)
mhd-bench mapping [--validate]                         # show/validate tagset mapping
mhd-bench evaluate [corpus_dir] --adapter NAME [...]   # run evaluation
mhd-bench compare [corpus_dir] --models a,b [...]      # compare cached results
```

Corpus directory is auto-detected if omitted.

| Flag | Description |
|------|-------------|
| `--adapter` | `passthrough`, `majority`, `api`, `cli` |
| `--models A,B` | Compare cached results from previous evaluate runs |
| `--subset N` | Evaluate on N representative documents |
| `--model NAME` | Model name for display and caching |
| `--cli-cmd CMD` | CLI command (for `--adapter cli`) |
| `--provider NAME` | `openai`, `gemini`, `mistral`, `groq` (for `--adapter api`) |
| `--api-key [VALUE]` | API key; bare flag prompts interactively |
| `--api-base URL` | Custom API base URL (for local models) |
| `--output PATH` | Save JSON results |
| `--continue-on-error` | Skip failed documents |
| `-v` | Debug logging |

## Documentation

| | |
|---|---|
| **Guides** | |
| [Getting Started](docs/guides/GETTING-STARTED.md) | Installation, first run, first model |
| [Troubleshooting](docs/guides/TROUBLESHOOTING.md) | Common errors and fixes |
| [Model Adapter Guide](docs/guides/MODEL-ADAPTER-GUIDE.md) | Add your own model (BERT, CRF, etc.) |
| **Reference** | |
| [Architecture](docs/ARCHITECTURE.md) | Pipeline, data model, modules |
| [Requirements](docs/REQUIREMENTS.md) | User stories, epics, success criteria |
| [Tagset Mapping](docs/TAGSET-MAPPING.md) | HiTS → MHDBDB mapping rationale |
| [MHDBDB Tagset](docs/MHDBDB-TAGSET.md) | Target: 16 evaluable tags |
| [HiTS Tagset](docs/HITS-TAGSET.md) | Source: 73 tags with frequencies |
| [CORA-XML Format](docs/CORA-XML-FORMAT.md) | ReM data format |
| [Research Context](docs/RESEARCH.md) | Related work, research gap |

## License

Benchmark code: CC BY-NC-SA 4.0. ReM corpus: CC BY-SA 4.0 (downloaded separately).
