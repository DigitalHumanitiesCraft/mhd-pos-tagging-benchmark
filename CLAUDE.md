# CLAUDE.md

## Project in One Paragraph

Model-agnostic benchmark for Part-of-Speech tagging of Middle High German (MHG) texts. Uses the ReM (Referenzkorpus Mittelhochdeutsch, v2.1) as ground truth with hand-annotated HiTS POS tags (73 tags in corpus). Maps HiTS → MHDBDB 19-tag tagset. Any POS tagger (LLM or classical) can be evaluated via a pluggable adapter interface. Outputs accuracy, per-tag P/R/F1, and confusion matrices. Built for a planned publication comparing Frontier LLMs vs. open-source models.

## Team

- **Michael** — University of Salzburg, MHDBDB project lead, medieval German studies
- **Christian** — DHCraft OG, technical lead, builds the benchmark tooling
- **Katharina** — Ruhr-Universität Bochum, computational linguistics, ReM expertise

## Sibling Project

The MHDBDB TEI repository (`../mhdbdb-tei-only/`) contains:
- ~670 TEI-encoded MHG texts with word-level POS annotations (19-tag MHDBDB tagset)
- A Gemini CLI skill (`pos-disambiguator`) for LLM-based POS disambiguation
- Detailed linguistic knowledge about MHG POS (error patterns, disambiguation rules)
- The skill lives at `../mhdbdb-tei-only/.gemini/skills/pos-disambiguator/SKILL.md`

Reference that project for tagset definitions, disambiguation heuristics, and known error patterns.

## Publication Context

- **Paper:** Frontier LLMs vs. open-source/self-trained models for MHG POS tagging
- **DFG network application:** Benchmark serves as demonstrator
- **Meeting 9.3.2026:** Team agreed on ReM as ground truth, Katharina found ~25 overlapping texts
- **Edition-matching problem:** Different editions between ReM and MHDBDB may affect comparability — deferred for now, philological review needed later (Michael to assign HiWi)
- **Next meeting:** 7.4.2026 (after Easter)

## ReM Data

- **Location:** `ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/` (407 XML files, gitignored)
- **Format:** CORA-XML (NOT standard TEI) — see `docs/CORA-XML-FORMAT.md`
- **Download:** https://www.linguistics.rub.de/rem/access/index.html (CORA-XML, 106 MB)
- **Also available:** TEI format (`ReM-v2.1_tei/`), JSON (`ReM-v2.1_json/`)
- **Citation:** Roussel, Adam; Klein, Thomas; Dipper, Stefanie; Wegera, Klaus-Peter; Wich-Reif, Claudia (2024). Referenzkorpus Mittelhochdeutsch (1050–1350), Version 2.1, https://www.linguistics.ruhr-uni-bochum.de/rem/. ISLRN 937-948-254-174-0.
- **ReM License:** CC BY-SA 4.0 (benchmark code is CC BY-NC-SA 4.0)

## Commands

```bash
pip install -e ".[dev]"              # Install with dev dependencies
pytest                                # Run tests
mhd-bench parse ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ --stats    # Parse + stats
mhd-bench mapping --validate --corpus-dir ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/  # Check all HiTS tags have mappings
mhd-bench evaluate --adapter passthrough   # Pipeline sanity check (should be 100%)
```

## Hard Constraints

- **Python 3.13+** with lxml
- **CC BY-NC-SA 4.0** license
- **ReM data is gitignored** — user downloads separately
- **results/ is gitignored** — benchmark outputs are local
- **Tagset mapping** (`src/mhd_pos_benchmark/mapping/hits_to_mhdbdb.yaml`) is the single source of truth for HiTS→MHDBDB conversion

## Key Architecture Decisions

- **Use `<tok_anno>` layer** (not `<tok_dipl>`) — POS tags live on tok_anno elements
- **Use `<pos>` tag** (instance-level, fine-grained like DDART, ADJA) — not `<pos_gen>` (generalized like DD, ADJ)
- **Multi-mod tokens** (clitics): one `<token>` can contain multiple `<tok_anno>` elements (e.g., "soltu" → "solt" VV + "u" PPER). Each tok_anno = one benchmark token.
- **Unmappable tags** (FM, punctuation) → excluded from evaluation, counted separately
- **Gold passthrough adapter** validates the pipeline (should produce 100% accuracy)

## Directory Layout

```
ReM-v2.1_coraxml/    # ReM corpus data (gitignored)
ReM-v2.1_tei/        # ReM TEI format (gitignored)
ReM-v2.1_json/       # ReM JSON format (gitignored)
docs/                 # Knowledge documentation
src/mhd_pos_benchmark/
  data/               # Parsers and data model
  mapping/            # HiTS→MHDBDB tagset mapping
  adapters/           # Model adapter interface + implementations
  evaluation/         # Metrics, comparator, reporting
tests/                # pytest tests
results/              # Benchmark output (gitignored)
```
