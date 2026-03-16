# Plan: MHD POS Tagging Benchmark

## Context

The MHDBDB project has developed a Gemini-based POS disambiguation skill for Middle High German texts (19-tag MHDBDB tagset). The team (Michael, Christian, Katharina) plans a publication comparing Frontier LLMs vs. open-source models for MHG POS tagging and needs systematic evaluation against a gold standard.

**Ground truth:** The ReM (Referenzkorpus Mittelhochdeutsch) provides hand-annotated POS tags using the HiTS tagset (~80 tags). CORA-XML data is freely downloadable. ~25 MHDBDB texts overlap with ReM (mostly epic genre).

**Goal:** A standalone, model-agnostic benchmark repository that can evaluate any POS tagger against ReM ground truth, with accuracy/F1/confusion metrics broken down by tag, text, and genre.

**Decisions made:**
- Standalone repo (no git submodule), relevant knowledge exported as docs
- Model-agnostic (pluggable adapter interface for any model)
- Edition-matching problem deferred (build pipeline first)
- CC BY-NC-SA 4.0 license

## Step 0: Context Export (Critical!)

Knowledge from this session that must be baked into the new repo so a fresh Claude session has full context:

### CLAUDE.md (new repo)
Project briefing for Claude Code in the new repo. Must contain:
- Project purpose: model-agnostic benchmark for MHG POS tagging against ReM ground truth
- Team: Michael (Salzburg, MHDBDB lead), Christian (DHCraft, tech lead), Katharina (Bochum/linguistics, ReM expertise)
- Publication goal: Frontier LLMs vs. open-source models for MHG POS
- DFG network application context (benchmark as demonstrator)
- Sibling project: `mhdbdb-tei-only` (same parent dir) — source of tagset knowledge, pos-disambiguator skill
- Hard constraints: Python 3.13+, CC BY-NC-SA 4.0, ReM data is gitignored (user downloads)
- Commands cheat sheet

### docs/MHDBDB-TAGSET.md
Export the full 19-tag tagset from SKILL.md including:
- Tag table (NOM, NAM, ADJ, ADV, DET, POS, PRO, PRP, NEG, NUM, CNJ, SCNJ, CCNJ, IPA, VRB, VEX, VEM, INJ, DIG)
- **All functional distinctions**: DET vs PRO (attribuierend/substituierend), VRB vs VEX (Partizip II test), als/wie (SCNJ vs ADV vs IPA), war (5-way ambiguity), haben/sin/werden heuristic
- **All error patterns**: NEG never PRO, sant=NAM before names, deictic daz=DET, kein/dekein/dehein=DET, vur war=ADV, MHG reinforced negation
- POS as separate class (morphological distinctiveness)
- Compound tag rules (morphological fusions only: VRB PRO, PRP DET)
- "ART" is NOT a valid tag

### docs/HITS-TAGSET.md
HiTS tagset reference (~80 tags):
- Full category hierarchy (ADJ*, AP*, AV*, CARD, D*, P*, PTK*, V*, N*, ITJ, FM, $)
- Key distinction: HiTS separates Determiners (D) and Pronouns (P) as main classes
- Dual annotation: lemma-related + instance-related tags
- Based on STTS but adapted for historical German
- Source: Dipper et al. 2013, "HiTS: ein Tagset für historische Sprachstufen des Deutschen"

### docs/TAGSET-MAPPING.md
The full mapping rationale including:
- Every HiTS → MHDBDB mapping with linguistic justification
- Ambiguous mappings (AVW → ADV/IPA, PW → PRO/IPA, ADJN → ADJ/NOM) with defaults
- Unmappable tags (FM, punctuation) → null
- The VA* → VEX limitation (documented overcount)
- KOKOM → ADV rationale (comparative particles, from SKILL.md)

### docs/OVERLAP-TABLE.md
Katharina's complete mapping table (from her email):
- 40 ReM entries → ~25 MHDBDB texts
- rem_id, rem_title, mhdbdb_id, mhdbdb_title
- Genre bias note (epic-heavy, minimal lyric coverage)
- Edition-matching status: "deferred — needs manual philological review"
- DES2/GSP note (Buch von guter Speise maps to two MHDBDB sigles)

### docs/CORA-XML-FORMAT.md
CORA-XML structure reference:
- `<token>` → `<dipl>` (diplomatic) + `<mod>` (modernized) layers
- POS tags on `<mod>`: `<pos tag="VVFIN"/>`
- Lemma on `<mod>`: `<lemma tag="sollen"/>`
- Multi-mod tokens (clitics): "soltu" → 2 mods ("solt" VVFIN + "u" PPER)
- Metadata in `<cora-header>` attributes
- Download: https://www.linguistics.rub.de/rem/access/index.html (CORA-XML, 106 MB)

### docs/IMPLEMENTATION-PLAN.md
This plan file, adapted for the new repo context.

### hits_to_mhdbdb.yaml (draft)
The full YAML tagset mapping from the Plan agent's output — ~80 entries with comments. This is the single most critical artifact to carry over.

### Meeting context (→ CLAUDE.md or memory)
- Meeting 9.3.2026: Michael, Christian, Katharina agreed on ReM as ground truth
- Katharina downloaded ReM data, found overlaps, noted edition-matching problem
- Michael to assign HiWi for edition comparison (deferred)
- Next meeting: 7.4.2026 (after Easter)
- Katharina unavailable 28.3.-7.4.
- Gemini 3.1 Pro shows ~100% on normalized texts, struggles with complex MHG
- ~20% of long texts still incomplete in MHDBDB disambiguation
- Claude Opus also tested, good results
- Publication: comparing frontier vs. open-source, documenting infrastructure questions

## Repo Setup

**Path:** `C:\Users\chstn\Desktop\data\DHCraft\Projekte\Git\mhd-pos-tagging-benchmark`

```
mhd-pos-tagging-benchmark/
├── README.md
├── LICENSE                          # CC BY-NC-SA 4.0
├── pyproject.toml                   # Python 3.13+, click, lxml, pyyaml, scikit-learn, rich
├── .gitignore
│
├── docs/
│   ├── MHDBDB-TAGSET.md            # 19-tag tagset (exported from SKILL.md)
│   ├── HITS-TAGSET.md              # HiTS tagset reference
│   ├── TAGSET-MAPPING.md           # Mapping rationale and edge cases
│   ├── MODEL-ADAPTER-GUIDE.md      # How to plug in a new model
│   └── OVERLAP-TABLE.md            # ReM ↔ MHDBDB text overlap (Katharina's table)
│
├── src/mhd_pos_benchmark/
│   ├── __init__.py
│   ├── cli.py                      # Click CLI entry point
│   ├── data/
│   │   ├── __init__.py
│   │   ├── corpus.py               # Token, Document dataclasses
│   │   └── rem_parser.py           # CORA-XML parser → Document objects
│   ├── mapping/
│   │   ├── __init__.py
│   │   ├── tagset_mapper.py        # Load YAML, map HiTS → MHDBDB
│   │   └── hits_to_mhdbdb.yaml     # The mapping definition
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract ModelAdapter interface
│   │   └── gold_passthrough.py     # Returns mapped ground truth (pipeline validation)
│   └── evaluation/
│       ├── __init__.py
│       ├── metrics.py              # Accuracy, P/R/F1, confusion matrix
│       ├── comparator.py           # Align predictions to ground truth
│       └── report.py               # Console + JSON + LaTeX output
│
├── data/                            # .gitignored, user populates locally
│   └── rem/                         # Extracted CORA-XML files
│
├── results/                         # .gitignored, benchmark output
│
├── tests/
│   ├── conftest.py
│   ├── test_rem_parser.py
│   ├── test_tagset_mapper.py
│   ├── test_metrics.py
│   └── fixtures/
│       └── sample_cora.xml          # Minimal CORA-XML for testing
│
└── notebooks/
    └── exploration.ipynb            # Optional: data exploration
```

## Pipeline (End-to-End Flow)

```
ReM CORA-XML files
    ↓  rem_parser.py
List[Document] with tokens + HiTS POS tags
    ↓  tagset_mapper.py (hits_to_mhdbdb.yaml)
Tokens with mapped MHDBDB-equivalent tags (ground truth)
    ↓  adapter.predict()
Model assigns MHDBDB POS tags to token sequences
    ↓  comparator.align()
Pairs: (ground_truth_tag, predicted_tag) per token
    ↓  metrics.compute()
Accuracy, per-tag P/R/F1, confusion matrix
    ↓  report.generate()
Console table / JSON / LaTeX
```

## Implementation Steps (Phase 1 — MVP)

### Step 1: Repo scaffold
- `git init`, `pyproject.toml`, `.gitignore`, `LICENSE`, `README.md`
- Dependencies: `lxml`, `click`, `pyyaml`, `scikit-learn`, `rich`, `tabulate`
- Dev deps: `pytest`, `ruff`, `pytest-cov`

### Step 2: Data model (`corpus.py`)
```python
@dataclass
class Token:
    id: str
    form_diplomatic: str       # dipl utf
    form_modernized: str       # mod utf/ascii
    pos_hits: str              # Original HiTS tag
    pos_mhdbdb: str | None     # Mapped MHDBDB tag (None = unmappable)
    lemma: str | None

@dataclass
class Document:
    id: str
    title: str | None
    genre: str | None
    tokens: list[Token]
    metadata: dict
```

### Step 3: CORA-XML parser (`rem_parser.py`)
- Parse `<token>` → `<mod>` elements (modernized layer, where POS tags live)
- One `<mod>` with `<pos tag="..."/>` = one Token
- Handle multi-mod tokens (clitics: "soltu" → "solt" + "u" = 2 tokens)
- Extract metadata from `<cora-header>` attributes
- **Key:** Use `<mod>` layer, not `<dipl>` — POS tags live on mod

### Step 4: Tagset mapping (`hits_to_mhdbdb.yaml` + `tagset_mapper.py`)
- YAML file with ~80 HiTS → 19 MHDBDB mappings
- `null` = unmappable (FM, punctuation) → excluded from eval
- `ambiguous_mappings` section documents context-dependent cases with defaults
- Key mappings:
  - `NA → NOM`, `NE → NAM`
  - `DD/DI/DG/DW → DET`, `DP → POS`
  - `PPER/PRF/PI/PG/PW/PD → PRO`
  - `PTKN → NEG`
  - `VA* → VEX`, `VM* → VEM`, `VV* → VRB`
  - `KON → CCNJ`, `KOUS/KOUI → SCNJ`, `KOKOM → ADV`
  - `CARD → NUM`, `ITJ → INJ`
- `tagset_mapper.py`: loads YAML, applies mapping, flags unmappable tokens
- CLI: `mhd-bench mapping --validate` checks for unmapped tags in actual data

### Step 5: Gold passthrough adapter (`gold_passthrough.py`)
- "Model" that returns the mapped ground truth tags
- Purpose: validate the pipeline (should produce 100% accuracy)
- Also usable to measure MHDBDB's own tags vs. ReM on overlap subset

### Step 6: Evaluation engine (`metrics.py`, `comparator.py`)
- `comparator.align()`: pairs ground truth + prediction per token, excludes unmappable
- `metrics.compute()`:
  - Overall accuracy
  - Per-tag precision, recall, F1 (via sklearn)
  - Macro-F1 and micro-F1
  - Confusion matrix (19×19)
  - Token counts: total, evaluated, excluded (with breakdown by exclusion reason)

### Step 7: Report generator (`report.py`)
- Console: rich table with per-tag metrics + summary
- JSON: machine-readable full results
- (LaTeX: Phase 2)

### Step 8: CLI (`cli.py`)
```bash
mhd-bench parse data/rem/ --stats          # Parse + show corpus statistics
mhd-bench mapping --validate               # Check all HiTS tags have mappings
mhd-bench evaluate --adapter passthrough    # Run gold passthrough (pipeline test)
mhd-bench evaluate --adapter gemini         # Run with LLM (Phase 2)
mhd-bench report results/run-001/           # Generate report from saved results
```

### Step 9: Tests
- `test_rem_parser.py`: parse fixture CORA-XML, verify token extraction
- `test_tagset_mapper.py`: verify all mappings, test unmappable handling
- `test_metrics.py`: verify accuracy/F1 computation on known data

### Step 10: Documentation
- Export MHDBDB 19-tag tagset from SKILL.md → `docs/MHDBDB-TAGSET.md`
- Document HiTS tagset → `docs/HITS-TAGSET.md`
- Write mapping rationale → `docs/TAGSET-MAPPING.md`
- Katharina's overlap table → `docs/OVERLAP-TABLE.md`

## Phase 2 (Later): LLM Adapters + Publication

- `gemini.py`, `openai.py`, `anthropic.py`, `ollama.py` adapters
- Shared prompt template (configurable, derived from SKILL.md knowledge)
- Result caching (JSONL per document+model+version)
- `mhd-bench compare` command for multi-model comparison
- LaTeX report output for paper
- Per-genre and per-difficulty breakdowns
- Error pattern analysis (top confused tag pairs)

## Known Challenges

1. **HiTS tag discovery:** Must empirically scan all ReM files for actual tags used, not just documented ones. `mapping --validate` handles this.
2. **VA* → VEX overcount:** HiTS always marks auxiliaries as VA*, but MHDBDB distinguishes VRB/VEX contextually. The mapping is correct for HiTS but may overcount VEX. Document as known limitation.
3. **Tokenization for LLMs (Phase 2):** LLM adapters receive pre-tokenized forms and must return one tag per token. Prompt engineering needed.
4. **Genre metadata:** ReM may not consistently encode genre. May need manual CSV.
5. **Cost:** Frontier LLM evaluation over thousands of tokens. Implement caching.

## Verification

1. `mhd-bench parse data/rem/ --stats` shows correct token counts per file
2. `mhd-bench mapping --validate` reports 0 unmapped tags
3. `mhd-bench evaluate --adapter passthrough` produces 100% accuracy (pipeline sanity check)
4. `pytest` passes all tests
5. Console report shows per-tag P/R/F1 table with plausible numbers
