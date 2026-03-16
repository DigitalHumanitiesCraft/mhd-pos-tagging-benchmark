# CLAUDE.md

## Project in One Paragraph

**Which model tags Middle High German POS best?** This benchmark answers that question by enabling direct head-to-head comparison of any POS tagger against a validated ground truth. Uses the ReM (Referenzkorpus Mittelhochdeutsch, v2.1) with hand-annotated HiTS POS tags (73 tags), mapped to the MHDBDB 19-tag tagset. Technology-agnostic: the same adapter interface works for frontier LLMs (currently Gemini 3.1 Pro, Claude Opus 4.6), open-source models, encoder models, or classical taggers. Outputs accuracy, per-tag P/R/F1, and confusion matrices. Before this benchmark, there was no way to objectively compare — the ground truth pipeline makes it possible.

## Team

- **Michael** — TU Darmstadt, professor, medieval German studies
- **Christian** — DHCraft OG, technical lead, builds the benchmark tooling
- **Katharina** — University of Salzburg, MHDBDB project lead, computational linguistics, ReM expertise

## Sibling Project

The MHDBDB TEI repository (`../mhdbdb-tei-only/`) contains ~670 TEI-encoded MHG texts, a Gemini CLI skill (`pos-disambiguator`) for LLM-based POS disambiguation, and detailed linguistic knowledge. Reference it for tagset definitions, disambiguation heuristics, and error patterns.

## Publication Context

- **Paper:** Head-to-head comparison of POS taggers for MHG (models interchangeable, ground truth enables the comparison)
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
