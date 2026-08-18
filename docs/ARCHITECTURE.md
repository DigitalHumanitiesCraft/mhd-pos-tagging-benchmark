# Architecture — MHD POS Tagging Benchmark

Current state of the system. Updated when the code changes.

**Related:** [REQUIREMENTS.md](REQUIREMENTS.md) (what we need)

## Pipeline

```
ReM CORA-XML files (406 docs, 2.58M tokens)
       │
       ▼
  ┌─────────────┐
  │ rem_parser   │  Parse <tok_anno> + <pos tag="..."/>
  │              │  Handle multi-tok_anno (clitics)
  │              │  Extract metadata from <header>
  └──────┬──────┘
         │ List[Document]
         ▼
  ┌─────────────┐
  │ tagset_mapper│  YAML: 73 HiTS → 16 MHDBDB tags + null
  │              │  Sets token.pos_mhdbdb
  │              │  null = excluded from evaluation
  └──────┬──────┘
         │ List[Document] (with pos_mhdbdb set)
         ▼
  ┌─────────────┐
  │ adapter      │  Any POS tagger: LLM, encoder, classical
  │  .predict()  │  Input: Document → Output: list[str]
  │              │  One tag per mappable token
  └──────┬──────┘
         │ list[str] predictions
         ▼
  ┌─────────────┐
  │ comparator   │  Align (gold, predicted) per token
  │  .align()    │  Skip excluded tokens
  └──────┬──────┘
         │ List[AlignmentResult]
         ▼
  ┌─────────────┐
  │ metrics      │  Accuracy, per-tag P/R/F1, confusion matrix
  │  .compute()  │  Via sklearn
  └──────┬──────┘
         │ EvaluationResult
         ▼
  ┌─────────────┐
  │ report       │  Console (rich), JSON
  │              │  (LaTeX: Phase 2)
  └─────────────┘
```

## Data Model

### Token

One annotatable unit = one `<tok_anno>` element from CORA-XML.

```python
Token:
    id: str                    # e.g., "t1_m1"
    form_diplomatic: str       # from <tok_dipl utf="...">
    form_modernized: str       # from <tok_anno utf="...">
    pos_hits: str              # from <pos tag="..."> — e.g., "DDART", "VVFIN"
    pos_mhdbdb: str | None     # mapped tag — e.g., "DET", "VRB", or None (excluded)
    lemma: str | None          # from <lemma tag="...">
    is_multimod: bool          # True if sub-token of a clitic (>1 tok_anno)

    .form_for_tagging → str    # modernized for clitics, diplomatic otherwise
    .is_mappable → bool        # pos_mhdbdb is not None
```

### Document

One CORA-XML file.

```python
Document:
    id: str                    # from <text id="...">
    title: str | None          # from <header><title>
    genre: str | None          # from <header><genre> — "V", "P", "PV"
    tokens: list[Token]        # all tok_anno elements
    metadata: dict[str, str]   # all header fields

    .mappable_tokens → list[Token]   # included in evaluation
    .excluded_tokens → list[Token]   # FM, punctuation, untagged, KO*
```

### Multi-Mod Tokens (Clitics)

One `<token>` can contain multiple `<tok_anno>` elements:

```xml
<token id="t6" trans="inder">          <!-- written form -->
  <tok_anno id="t6_m1" utf="in">      → Token(pos_hits="APPR", pos_mhdbdb="PRP")
  <tok_anno id="t6_m2" utf="der">     → Token(pos_hits="DDART", pos_mhdbdb="DET")
</token>
```

Each `<tok_anno>` = one Token in our model. The parser flattens these.

## Adapter Interface

```python
class ModelAdapter(ABC):
    name: str                                    # e.g., "gold-passthrough", "gemini-3.1-pro"
    def predict(self, document: Document) -> list[str]
        # Must return exactly len(document.mappable_tokens) tags
```

Technology-agnostic: the adapter wraps whatever tagger you have. Examples:

| Tagger Type | Adapter receives | Adapter does | Adapter returns |
|------------|-----------------|-------------|-----------------|
| LLM (API) | Document with tokens | Build prompt, call API, parse response | list of MHDBDB tags |
| Encoder (BERT) | Document with tokens | Tokenize, run model, decode labels | list of MHDBDB tags |
| Classical (CRF) | Document with tokens | Extract features, run model | list of MHDBDB tags |
| Gold passthrough | Document with mapped tags | Return `token.pos_mhdbdb` | list of MHDBDB tags |

The adapter contract: **input = Document, output = one MHDBDB tag per mappable token, in order.**

## Tagset Mapping

Single source of truth: `src/mhd_pos_benchmark/mapping/hits_to_mhdbdb.yaml`

```
73 HiTS tags (ReM v2.1)  →  16 MHDBDB tags + null (excluded)
```

Suffix system (confirmed by Katharina):

| Suffix | Function | Mapping pattern |
|--------|----------|----------------|
| `A` | attributiv | → DET (for D-categories), NUM (for CARD) |
| `S` | substituierend | → PRO (for D-categories), NUM (for CARD) |
| `D` | adverbial | → ADV (for D-categories), NUM (for CARD) |
| `N` | nominalisiert | → PRO (for D-categories), NUM (for CARD) |
| `ART` | article use | → DET |

Exception: `DPOS*` always → POS regardless of suffix.

### Coverage

| Category | Tokens | % of corpus |
|----------|-------:|------------:|
| Mappable (→ MHDBDB tag) | 2,122,630 | 82.3% |
| Excluded: `$_` punctuation | 286,202 | 11.1% |
| Excluded: `--` untagged | 121,808 | 4.7% |
| Excluded: `FM` foreign | 26,163 | 1.0% |
| Excluded: `KO*` ambiguous | 22,473 | 0.9% |
| **Total** | **2,579,276** | **100%** |

### MHDBDB Tags Without HiTS Source

| Tag | Reason | Impact |
|-----|--------|--------|
| IPA | No interrogative particle tag in HiTS; candidates (AVW, PW) default to ADV/PRO | Systematic undercount |
| CNJ | No generic conjunction in HiTS; KO* could be source but excluded | 0 support |
| DIG | Roman numerals not tagged separately in ReM | 0 support |

## Module Map

```
src/mhd_pos_benchmark/
├── __init__.py              # version
├── cli.py                   # Click CLI: parse, mapping, evaluate, compare
├── data/
│   ├── corpus.py            # Token, Document dataclasses
│   ├── rem_parser.py        # CORA-XML → Document (lxml)
│   └── subset.py            # Genre-stratified sampling + explicit ID selection
├── mapping/
│   ├── tagset_mapper.py     # Load YAML, map tags, find unmapped
│   └── hits_to_mhdbdb.yaml  # 73 mappings (v0.2.0)
├── adapters/
│   ├── base.py              # ModelAdapter ABC
│   ├── gold_passthrough.py  # Returns mapped ground truth
│   ├── majority_class.py    # Most-frequent-tag baseline (18.4%)
│   ├── generic_api.py       # Any OpenAI-compatible API (OpenAI, Gemini, Mistral, Groq, local)
│   ├── generic_cli.py       # Any CLI tool (claude, gemini, codex, copilot, vibe, ...)
│   ├── cli_presets.py       # Built-in CLI presets (claude, antigravity, gemini, codex, copilot) + cli-profiles.yaml loader
│   ├── cached.py            # CachedAdapter: load predictions from previous evaluate runs
│   ├── prompt_template.py   # Shared prompt + response parsing for all LLMs
│   └── cache.py             # JSONL result cache with config hash
└── evaluation/
    ├── comparator.py        # Align gold vs predicted, continue-on-error
    ├── metrics.py           # Accuracy, P/R/F1, confusion (sklearn)
    └── report.py            # Console (rich) + JSON output
```

## CLI

```bash
mhd-bench parse <corpus_dir> [--stats]
mhd-bench mapping [--validate --corpus-dir ...]
mhd-bench evaluate <corpus_dir> --adapter NAME [--subset N | --documents IDs] [--chunk-size N] [--api-key] [-v]
mhd-bench compare <corpus_dir> --adapters a,b [--subset N | --documents IDs] [--api-key] [-v]
```

Adapters: `passthrough`, `majority`, `api`, `cli`

### Selecting documents

`--subset N` samples the corpus genre-stratified and deterministically for a
given N. It is meant for exploration. The sample is a function of the corpus and
of the allocation code, so it moves when either changes: during the 2026-08-18
session, `--subset 8` returned M106, M351 and M408 while the cached Gemini run
from March covered M255, M114 and M121S. The cached run had become unreachable
through `--subset` without anything reporting an error.

`--documents M033,M174,...` names the texts instead. Unknown IDs abort the run
rather than being skipped, since dropping one would change what a published
number covers. Three mechanisms keep a selection traceable:

- every `--subset` run prints the `--documents` line that repeats it exactly
- every saved JSON result carries `document_ids`
- `compare` warns when the models in a table were not scored on the same
  documents, and prints the `--documents` line for the shared set
  (`coverage_mismatch` in `evaluation/comparator.py`)

### Chunk size

`--chunk-size N` sets how many tokens go into one model call (default 200).
The value is part of the cache config hash, so changing it invalidates cached
results for that model.

Measured 2026-08-18 on M021 (1.364 tokens) against Claude Opus 5:

| chunk | calls | seconds | accuracy |
|---|---|---|---|
| 200 | 7 | 385,8 | 0,8981 |
| 500 | 3 | 365,1 | 0,8930 |
| 1364 (whole document) | 1 | 363,3 | 0,9135 |

Three findings, none of which was obvious beforehand:

1. **Chunk size changes the result.** 1,5 accuracy points separate the extremes,
   so it is a confounder: two models are only comparable at the same chunk size.
   That is enforced through the cache config hash, and `compare` warns when
   cached runs carry different hashes.
2. **Larger chunks are not cheaper.** Per-call token usage, same model:
   200 tokens per call cost 4.582 in / 3.505 out, 500 tokens per call cost
   6.306 in / 10.649 out. Bigger chunks save harness overhead on the input side
   but provoke disproportionately more reasoning on the output side, which is
   the more expensive half. Over the 8-document set: 192k in / 147k out at
   chunk 200 versus 114k in / 192k out at chunk 500, which at Opus 5 rates is
   $4,64 against $5,36.
3. **Wall-clock is flat.** Fewer, longer calls take about as long as many short
   ones, so there is no speed argument either way.

The default therefore stays at 200. Larger chunks buy accuracy, not savings,
and that trade should be a deliberate, documented choice rather than a default.

Per-call time scales with chunk size, so the CLI adapter's timeout does too
(`max(300, chunk_size * 0.8)` seconds). The former fixed 300 s would have killed
every attempt at chunk 1364, which took 363 s.

`--api-key`: bare flag → masked interactive prompt; with value → use directly; omitted → env var fallback. Key never touches disk.

## Adapter Hierarchy

```
ModelAdapter (ABC)
├── GoldPassthroughAdapter          # Pipeline validation (100%)
├── MajorityClassAdapter            # Baseline (most frequent tag)
├── GenericApiAdapter               # Any OpenAI-compatible API (openai SDK)
│                                   #   Provider presets: openai, gemini, mistral, groq
├── GenericCliAdapter               # Any CLI tool (subprocess + stdin)
│                                   #   Presets: claude, antigravity, gemini, codex, copilot
│                                   #   Runs in an empty temp dir (harness isolation)
│                                   #   User override: cli-profiles.yaml (optional, same schema)
└── CachedAdapter                   # Load predictions from previous evaluate runs
```

### Generic API Adapter (`--adapter api`)

Works with any provider offering an OpenAI-compatible chat completions endpoint.
Uses the `openai` SDK with provider-specific base URLs.

Model IDs below were verified on 2026-08-18. They change often; check the
provider's model list before citing a run.

```bash
# OpenAI
mhd-bench evaluate corpus/ --adapter api --provider openai --model gpt-5.6 --api-key sk-...

# Gemini (via OpenAI-compatible endpoint)
mhd-bench evaluate corpus/ --adapter api --provider gemini --model gemini-3.1-pro-preview --api-key AI...

# Mistral
mhd-bench evaluate corpus/ --adapter api --provider mistral --model mistral-large-latest --api-key ...

# Groq
mhd-bench evaluate corpus/ --adapter api --provider groq --model openai/gpt-oss-120b --api-key ...

# Local (ollama, vLLM), no API key needed
mhd-bench evaluate corpus/ --adapter api --api-base http://localhost:11434/v1 --model llama3
```

### Generic CLI Adapter (`--adapter cli`)

For any CLI tool with a flat-rate subscription (no API key needed).
Each preset knows per-tool specifics: system prompt delivery (flag vs embed), prompt delivery (stdin vs argument), response format (raw vs JSON key), extra flags, and whether the call needs an isolated working directory.

```bash
# Using presets (recommended)
mhd-bench evaluate corpus/ --adapter cli --preset claude --model claude-opus-5
mhd-bench evaluate corpus/ --adapter cli --preset antigravity --model "Gemini 3.1 Pro (High)"
mhd-bench evaluate corpus/ --adapter cli --preset gemini --model gemini-3.1-pro-preview
mhd-bench evaluate corpus/ --adapter cli --preset codex --model gpt-5.6-sol

# Escape hatch for unknown CLIs
mhd-bench evaluate corpus/ --adapter cli --cli-cmd "vibe --prompt"
```

Users can define custom CLI profiles in `cli-profiles.yaml` (same schema as built-in presets).

#### CLI presets

Coding CLIs are agentic harnesses, not bare model endpoints. Invoked naively they
load project instruction files, MCP servers, skills and tool definitions into
every request. For a benchmark that produces two separate defects, both measured
on 2026-08-18 against Claude Code 2.1.234:

1. **Contamination.** A `claude -p` call started inside this repository could
   name the benchmark's corpus, its version and its tagset. The model under test
   was reading the benchmark's own documentation, even though `--system-prompt`
   had replaced the default system prompt.
2. **Cost.** The same call carried 25.782 input tokens of harness context per
   chunk. At `chunk_size=200`, a 12.700-token document needs 64 calls, so roughly
   1,6 million tokens per document go to overhead rather than to tagging.

Two mechanisms address this, both encoded in the presets:

| Mechanism | Effect |
|---|---|
| `--tools "" --strict-mcp-config` in the command template | 25.782 → 1.814 input tokens per call |
| `isolate_cwd` (subprocess runs in an empty temp dir) | Probe answers NO-CONTEXT instead of describing the project |

The two flags only work together. Measured individually: `--tools ""` alone
produced 31.589 tokens, `--strict-mcp-config` alone 24.732. Only the combination
drops to 1.814.

`--bare` would be the cleaner isolation switch, but it never reads OAuth
credentials: with a subscription login it fails with "Not logged in". It is
therefore only an option for users who have an `ANTHROPIC_API_KEY`.

Presets carry a `caveat` field where something about them is not
straightforward; `evaluate` prints it before the run.

#### Subscription access, verified 2026-08-18

Every mainstream coding CLI authenticates against a subscription rather than an
API key, which matters for a benchmark meant to be reproducible by colleagues
without an API budget.

| Preset | Auth | Preset default | 10-token probe |
|---|---|---|---|
| `claude` | Claude subscription | `claude-opus-5` | 5,1 s |
| `codex` | ChatGPT plan (no API key) | `gpt-5.6-sol` | 5,7 s |
| `antigravity` | Google account | `gemini-3.1-pro-high` | 11,7 s |
| `copilot` | GitHub Copilot subscription | `claude-sonnet-4.6` | 7,5 s |
| `gemini` | paid `GEMINI_API_KEY` only | (none) | consumer tier retired 2026-06-18 |

All four working paths run on a subscription, so a full four-way comparison
costs nothing beyond quota. That matters for the paper: colleagues can reproduce
a run without an API budget.

**Model IDs are per tool, not per model.** Do not carry API model IDs over into
a preset, and do not guess: every tool publishes its own list, and the lists
below were read from the tools themselves on 2026-08-18, not from documentation.

**Codex** (`~/.codex/models_cache.json`, which the CLI refreshes from the
account; client 0.147.0), in the tool's own priority order:

| ID | Display name | Default reasoning | Context |
|---|---|---|---|
| `gpt-5.6-sol` | GPT-5.6-Sol | low | 272k (max 872k) |
| `gpt-5.6-terra` | GPT-5.6-Terra | medium | 272k (max 872k) |
| `gpt-5.6-luna` | GPT-5.6-Luna | medium | 272k (max 872k) |
| `gpt-5.5` | GPT-5.5 | medium | 272k |
| `gpt-5.4` | GPT-5.4 | medium | 272k (max 1M) |
| `gpt-5.4-mini` | GPT-5.4-Mini | medium | 272k |
| `gpt-5.3-codex-spark` | GPT-5.3-Codex-Spark | high | 128k |

A family name without a variant (`gpt-5.6`) does not exist here, and neither do
the older `*-codex` names apart from Codex-Spark: both are rejected as "not
supported when using Codex with a ChatGPT account". Reasoning level is a
separate setting, not part of the ID.

**Antigravity** (`agy models`): the ID is the left column, the display name the
right one, and reasoning depth is part of the ID. Available:
`gemini-3.7-flash-{high,medium,low}`, `gemini-3.6-flash-{high,medium,low}`,
`gemini-3.5-flash-{high,medium,low}`, `gemini-3.1-pro-{high,low}` (Pro has no
medium), `claude-sonnet-4-6`, `claude-opus-4-6-thinking`, `gpt-oss-120b-medium`.

**Copilot** (CLI 1.0.80, probed name by name against the subscription, since the
CLI validates `--model` only when a session starts): `claude-sonnet-4.6`,
`claude-sonnet-4.5`, `claude-haiku-4.5`, `gpt-5.4`, `gpt-5.3-codex`,
`gpt-5-mini`, `gemini-3.1-pro-preview`, `gemini-3.5-flash`. Rejected: every
`claude-opus` name, `gpt-5.6`, `gpt-5.5`, `gpt-4.1`, `gpt-5.4-codex`,
`gpt-5.2-codex`, `gemini-3-pro`, `gemini-3.1-pro`. Copilot's `auto` picks a
model on its own (Claude Haiku 4.5 when tested) and must never be used for a
published number, which is why the preset defaults to a named model.

Two consequences for the study design:

- The same model is reachable through several subscriptions. Claude Sonnet 4.6
  runs via Copilot and via Antigravity, Gemini 3.1 Pro Preview via Copilot and
  via the Gemini API. If a model scores differently depending on the route, the
  benchmark is measuring the harness rather than the model, so route belongs in
  the results table next to the model name.
- Model lists move fast. Re-read them from the tools before a publication run
  rather than trusting this table: `agy models`, `~/.codex/models_cache.json`,
  and a probe sweep for Copilot.

Two invocation quirks, both silent failures rather than errors:

- Codex needs `--skip-git-repo-check`, because `isolate_cwd` runs the call in an
  empty temp directory, which it otherwise refuses as untrusted.
- Antigravity needs `-p` last with the prompt directly after it. Anywhere else,
  or via stdin, it ignores both the prompt and `--model`, and answers with a
  greeting from its default model. Exit code 0.

#### npm wrappers on Windows

CLIs installed through npm are batch wrappers, and cmd.exe mangles a long
multi-line argument passed through one. Measured 2026-08-18: through
`copilot.CMD` the Copilot CLI received only the first line of the tagging prompt
and returned nothing usable; the identical call through `node npm-loader.js`
returned correct tags. The adapter therefore unwraps `.CMD`/`.BAT` launchers to
a direct `node <script>` call, but only for presets that deliver the prompt as
an argument. Presets using stdin are unaffected and keep the wrapper.

Related: `resolve_real_executable` in `doctor.py` looks past editor-bundled
launchers when resolving a CLI on PATH, so neither `doctor` nor the adapter can
end up measuring the VS Code Copilot shim.

### Custom Adapters

For fine-tuned BERT, CRF, or other local models — implement the `ModelAdapter` interface:

```python
class MyModelAdapter(ModelAdapter):
    @property
    def name(self) -> str:
        return "my-model"

    def predict(self, document: Document) -> list[str]:
        # Return one MHDBDB tag per document.mappable_tokens
        return [self.model.predict(t.form_for_tagging) for t in document.mappable_tokens]
```

## Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| lxml | CORA-XML parsing | ≥5.0 |
| click | CLI framework | ≥8.1 |
| pyyaml | YAML mapping file | ≥6.0 |
| scikit-learn | Metrics (P/R/F1, confusion) | ≥1.4 |
| rich | Console tables | ≥13.0 |
| openai | LLM API adapter (optional) | ≥1.0 |

Python ≥3.13 required.

## Tests

130 tests in `tests/`:
- `test_rem_parser.py` (6) — fixture-based, covers simple + multi-mod + metadata
- `test_tagset_mapper.py` (12) — all suffix patterns, unmappable, unknown tags
- `test_metrics.py` (4) — perfect/partial accuracy, token counts, confusion shape
- `test_cli_adapters.py` (8) — parse_tag_response: valid/invalid JSON, fences, counts, trailing text
- `test_generic_api.py` (11) — GenericApiAdapter: providers, predict, caching, chunking, retries, local endpoint
- `test_generic_cli.py` (26) — GenericCliAdapter: predict, stdin prompt, retries, caching, chunking, working-directory isolation, preset commands
- `test_cli.py` (21) — CLI integration via CliRunner: parse, mapping, evaluate, compare, version, document selection, chunk size
- `test_report.py` (5) — print_report, save_json, JSON schema, directory creation
- `test_comparator.py` (14) — align_document, align_corpus, error handling, progress callback, coverage mismatch detection
- `test_subset.py` (16) — stratification, determinism, edge cases, explicit ID selection and its error messages
- `test_prompt_template.py` (7) — build_tagging_prompt, chunked prompts, numbering

Fixture: `tests/fixtures/sample_cora.xml` (9 tokens: NA, VVFIN, APPR, DDART, NA, clitic APPR+DDART, $_, FM)
