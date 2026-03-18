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
│   └── subset.py            # Genre-stratified subset selection
├── mapping/
│   ├── tagset_mapper.py     # Load YAML, map tags, find unmapped
│   └── hits_to_mhdbdb.yaml  # 73 mappings (v0.2.0)
├── adapters/
│   ├── base.py              # ModelAdapter ABC
│   ├── gold_passthrough.py  # Returns mapped ground truth
│   ├── majority_class.py    # Most-frequent-tag baseline (18.4%)
│   ├── gemini.py            # Gemini API adapter (google-genai SDK)
│   ├── cli_base.py          # Shared base for CLI-subprocess adapters
│   ├── claude_cli.py        # Claude Code CLI adapter (claude -p)
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
mhd-bench evaluate <corpus_dir> --adapter NAME [--subset N] [--api-key] [-v]
mhd-bench compare <corpus_dir> --adapters a,b [--subset N] [--api-key] [-v]
```

Adapters: `passthrough`, `majority`, `gemini`, `claude-cli`

`--api-key`: bare flag → masked interactive prompt; with value → use directly; omitted → env var fallback. Key never touches disk.

## Adapter Hierarchy

```
ModelAdapter (ABC)
├── GoldPassthroughAdapter          # Pipeline validation (100%)
├── MajorityClassAdapter            # Baseline (most frequent tag)
├── GeminiAdapter (API)             # google-genai SDK, needs GEMINI_API_KEY
└── CliLlmAdapter (ABC)             # Subprocess-based, subscription auth
    └── ClaudeCliAdapter            # claude -p --model opus (default)
```

## Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| lxml | CORA-XML parsing | ≥5.0 |
| click | CLI framework | ≥8.1 |
| pyyaml | YAML mapping file | ≥6.0 |
| scikit-learn | Metrics (P/R/F1, confusion) | ≥1.4 |
| rich | Console tables | ≥13.0 |
| tabulate | Table formatting | ≥0.9 |
| google-genai | Gemini API (optional) | ≥1.0 |

Python ≥3.13 required.

## Tests

65 tests in `tests/`:
- `test_rem_parser.py` (6) — fixture-based, covers simple + multi-mod + metadata
- `test_tagset_mapper.py` (12) — all suffix patterns, unmappable, unknown tags
- `test_metrics.py` (4) — perfect/partial accuracy, token counts, confusion shape
- `test_cli_adapters.py` (16) — parse_tag_response (6), ClaudeCliAdapter (10): predict, retry, timeout, cache, chunking
- `test_gemini_adapter.py` (8) — name, predict, caching, chunking, API key, retries (mocked SDK)
- `test_cli.py` (13) — CLI integration via CliRunner: parse, mapping, evaluate, compare, version
- `test_report.py` (5) — print_report, save_json, JSON schema, directory creation

Fixture: `tests/fixtures/sample_cora.xml` (9 tokens: NA, VVFIN, APPR, DDART, NA, clitic APPR+DDART, $_, FM)
