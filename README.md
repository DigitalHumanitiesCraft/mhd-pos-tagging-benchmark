# MHD POS Tagging Benchmark

Model-agnostic benchmark for Part-of-Speech tagging of Middle High German texts.

Uses the [ReM (Referenzkorpus Mittelhochdeutsch)](https://www.linguistics.rub.de/rem/) as ground truth with hand-annotated HiTS POS tags, mapped to the MHDBDB tagset (16 evaluable tags). Evaluates **any** POS tagger — LLM, encoder model, classical tagger — via a pluggable adapter interface. Reports accuracy, per-tag precision/recall/F1, and confusion matrices.

## Setup

```bash
# 1. Clone and install
git clone https://github.com/DigitalHumanitiesCraft/mhd-pos-tagging-benchmark.git
cd mhd-pos-tagging-benchmark
pip install -e ".[dev]"

# 2. Download ReM corpus (106 MB, gitignored)
# From: https://www.linguistics.rub.de/rem/access/index.html
# Extract so that ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/*.xml exists

# 3. Verify: parse corpus and show stats
mhd-bench parse ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ --stats

# 4. Sanity check: gold passthrough = 100% accuracy
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter passthrough --subset 3
```

## Evaluate a Model

### Via CLI (flat-rate subscription, no API key)

Works with any CLI tool that accepts a prompt: Claude Code, Gemini CLI, Codex, Copilot, Vibe CLI.

```bash
# Claude Opus 4.6
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter cli \
  --cli-cmd "claude -p --model opus" \
  --model claude-opus-4.6 \
  --subset 3

# Gemini 3.1 Pro Preview
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter cli \
  --cli-cmd "gemini -m gemini-3.1-pro-preview -p" \
  --model gemini-3.1-pro-preview \
  --subset 3

# OpenAI Codex CLI
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter cli \
  --cli-cmd "codex exec" \
  --model codex \
  --subset 3
```

### Via API (with API key)

Works with any OpenAI-compatible API: OpenAI, Gemini, Mistral, Groq, local models (ollama/vLLM).

```bash
# OpenAI GPT-4o
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter api \
  --provider openai \
  --model gpt-4o \
  --api-key sk-... \
  --subset 3

# Gemini 2.5 Pro (via OpenAI-compatible endpoint)
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter api \
  --provider gemini \
  --model gemini-2.5-pro \
  --api-key AI... \
  --subset 3

# Local model via ollama (no API key needed)
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter api \
  --api-base http://localhost:11434/v1 \
  --model llama3 \
  --subset 3
```

### Via custom adapter (BERT, CRF, etc.)

Implement the `ModelAdapter` interface — see [MODEL-ADAPTER-GUIDE.md](docs/MODEL-ADAPTER-GUIDE.md) for copy-paste examples (BERT, CRF, dictionary lookup).

## Compare Models Head-to-Head

The `compare` command evaluates multiple adapters on the same documents and prints a side-by-side table:

```bash
mhd-bench compare ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapters passthrough,majority \
  --subset 3
```

## Example: Claude Opus 4.6 vs Gemini 3.1 Pro Preview

Real output from `--subset 1` on document M084L (13 tokens, "Mit dise salmen den almahtigen got..."):

```
$ mhd-bench evaluate corpus/ --adapter cli \
    --cli-cmd "claude -p --model opus" --model claude-opus-4.6 --subset 1

Parsing corpus from corpus/...
Parsed 406 documents

Subset selected:
1 documents, 13 mappable tokens

Running evaluation with adapter: claude-opus-4.6...
Evaluating ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:05

                Summary
┌──────────────────┬──────────────┐
│ Documents        │            1 │
│ Total tokens     │           20 │
│ Evaluated tokens │           13 │
│ Excluded tokens  │   7 (35.0%)  │
│ Accuracy         │       0.9231 │
│ Macro-F1         │       0.9048 │
│ Micro-F1         │       0.9231 │
└──────────────────┴──────────────┘
```

```
$ mhd-bench evaluate corpus/ --adapter cli \
    --cli-cmd "gemini -m gemini-3.1-pro-preview -p" \
    --model gemini-3.1-pro-preview --subset 1

                Summary
┌──────────────────┬──────────────┐
│ Accuracy         │       1.0000 │
│ Macro-F1         │       1.0000 │
│ Micro-F1         │       1.0000 │
└──────────────────┴──────────────┘
```

**Token-level comparison:**

| Token | Gold | Claude Opus 4.6 | Gemini 3.1 Pro |
|-------|------|-----------------|----------------|
| Mit | PRP | PRP | PRP |
| diſe | DET | DET | DET |
| ſalmen | NOM | NOM | NOM |
| den | DET | DET | DET |
| almah[...] | ADJ | ADJ | ADJ |
| got | NOM | NOM | NOM |
| **wan** | **SCNJ** | **CCNJ** | **SCNJ** |
| do | ADV | ADV | ADV |
| ſprach | VRB | VRB | VRB |
| an | PRP | PRP | PRP |
| dem | PRO | PRO | PRO |
| er | PRO | PRO | PRO |
| hiêch | VRB | VRB | VRB |

Gemini 3.1 Pro correctly identifies `wan` ("denn/weil") as a subordinating conjunction (SCNJ), while Claude Opus misclassifies it as coordinating (CCNJ).

## Output

Results are cached in `results/<model-name>/predictions.jsonl` and reused on re-runs. Use `--output results.json` to save metrics:

```bash
mhd-bench evaluate corpus/ --adapter cli \
  --cli-cmd "claude -p --model opus" --model claude-opus-4.6 \
  --subset 3 --output results/claude-opus-4.6.json
```

The JSON contains accuracy, per-tag P/R/F1, and the full confusion matrix.

## CLI Reference

```bash
mhd-bench parse <corpus_dir> [--stats]
mhd-bench mapping [--validate --corpus-dir <dir>]
mhd-bench evaluate <corpus_dir> --adapter NAME [OPTIONS]
mhd-bench compare <corpus_dir> --adapters a,b [OPTIONS]
```

**Common options:**

| Flag | Description |
|------|-------------|
| `--adapter` | `passthrough`, `majority`, `api`, `cli` |
| `--subset N` | Evaluate on N representative documents (fast prototyping) |
| `--model NAME` | Model name for display and caching |
| `--cli-cmd CMD` | CLI command (for `--adapter cli`) |
| `--provider NAME` | API provider: `openai`, `gemini`, `mistral`, `groq` (for `--adapter api`) |
| `--api-key VALUE` | API key (bare `--api-key` prompts interactively, masked) |
| `--api-base URL` | Custom API base URL (for local models) |
| `--output PATH` | Save JSON results |
| `--continue-on-error` | Skip failed documents instead of aborting |
| `-v` | Verbose/debug logging |

## Documentation

| Document | Content |
|----------|---------|
| [MODEL-ADAPTER-GUIDE.md](docs/MODEL-ADAPTER-GUIDE.md) | How to add your own model (BERT, CRF, etc.) |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Pipeline, data model, adapter interface, modules |
| [REQUIREMENTS.md](docs/REQUIREMENTS.md) | User stories, epics, success criteria |
| [MHDBDB-TAGSET.md](docs/MHDBDB-TAGSET.md) | Target tagset: 16 evaluable MHDBDB tags |
| [HITS-TAGSET.md](docs/HITS-TAGSET.md) | Source HiTS tagset — all 73 tags with frequencies |
| [TAGSET-MAPPING.md](docs/TAGSET-MAPPING.md) | HiTS → MHDBDB mapping rationale |
| [CORA-XML-FORMAT.md](docs/CORA-XML-FORMAT.md) | ReM data format reference |
| [RESEARCH.md](docs/RESEARCH.md) | Academic context, related work |
| [JOURNAL.md](docs/JOURNAL.md) | Decision log |

## License

CC BY-NC-SA 4.0
