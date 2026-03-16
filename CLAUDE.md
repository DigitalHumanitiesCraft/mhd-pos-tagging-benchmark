# CLAUDE.md

## Project in One Paragraph

Model-agnostic benchmark for Part-of-Speech tagging of Middle High German (MHG) texts. Uses the ReM (Referenzkorpus Mittelhochdeutsch, v2.1) as ground truth with hand-annotated HiTS POS tags (73 tags in corpus). Maps HiTS → MHDBDB 19-tag tagset. Any POS tagger (LLM, encoder model, classical) can be evaluated via a pluggable adapter interface. Outputs accuracy, per-tag P/R/F1, and confusion matrices. Built for a planned publication comparing models across technology categories.

## Team

- **Michael** — University of Salzburg, MHDBDB project lead, medieval German studies
- **Christian** — DHCraft OG, technical lead, builds the benchmark tooling
- **Katharina** — Ruhr-Universität Bochum, computational linguistics, ReM expertise

## Sibling Project

The MHDBDB TEI repository (`../mhdbdb-tei-only/`) contains ~670 TEI-encoded MHG texts, a Gemini CLI skill (`pos-disambiguator`) for LLM-based POS disambiguation, and detailed linguistic knowledge. Reference it for tagset definitions, disambiguation heuristics, and error patterns.

## Publication Context

- **Paper:** Frontier LLMs vs. open-source/self-trained models for MHG POS tagging
- **DFG network application:** Benchmark serves as demonstrator
- **Edition-matching problem:** Deferred — Michael to assign HiWi for philological review
- **Next meeting:** 7.4.2026

## ReM Data

- **Location:** `ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/` (407 files, gitignored)
- **Format:** CORA-XML — see [CORA-XML-FORMAT.md](docs/CORA-XML-FORMAT.md)
- **Download:** https://www.linguistics.rub.de/rem/access/index.html (106 MB)
- **Citation:** Roussel, Adam; Klein, Thomas; Dipper, Stefanie; Wegera, Klaus-Peter; Wich-Reif, Claudia (2024). Referenzkorpus Mittelhochdeutsch (1050–1350), Version 2.1. ISLRN 937-948-254-174-0.
- **ReM License:** CC BY-SA 4.0 (benchmark code is CC BY-NC-SA 4.0)

## Commands

```bash
pip install -e ".[dev]"
pytest
mhd-bench parse ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ --stats
mhd-bench mapping --validate --corpus-dir ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ --adapter passthrough
```

## Hard Constraints

- **Python 3.13+** with lxml
- **CC BY-NC-SA 4.0** license (benchmark code)
- **ReM data is gitignored** — user downloads separately
- **Tagset mapping YAML** is the single source of truth for HiTS→MHDBDB conversion
- **Technology-agnostic** — adapter interface must support any POS tagger, not just LLMs

## Documentation

Architecture, data model, pipeline → [ARCHITECTURE.md](docs/ARCHITECTURE.md)
Requirements, user stories → [REQUIREMENTS.md](docs/REQUIREMENTS.md)
All docs → [README.md](README.md)
