# CLAUDE.md

## Project in One Paragraph

**Which model tags Middle High German POS best?** This benchmark answers that question by enabling direct head-to-head comparison of any POS tagger against a validated ground truth. Uses the ReM (Referenzkorpus Mittelhochdeutsch, v2.1) with hand-annotated HiTS POS tags (73 tags), mapped to the MHDBDB tagset (19 defined, 16 evaluable — CNJ, IPA, DIG have no HiTS source). Technology-agnostic: two generic adapters (`--adapter api` for any OpenAI-compatible API, `--adapter cli` for any CLI tool) plus custom Python adapters. Tested with Claude Opus 4.6, Gemini 2.5 Pro, Gemini 3.1 Pro Preview. Outputs accuracy, per-tag P/R/F1, and confusion matrices. Before this benchmark, there was no way to objectively compare — the ground truth pipeline makes it possible.

## Team

- **Michael** (`michaelscho`) — TU Darmstadt, professor, medieval German studies
- **Christian** (`chsteiner`) — DHCraft OG, technical lead, builds the benchmark tooling
- **Katharina** (`wachauer`) — University of Salzburg, MHDBDB project lead, computational linguistics, ReM expertise

## Sibling Project

The MHDBDB TEI repository (`../mhdbdb-tei-only/`) contains ~670 TEI-encoded MHG texts, a Gemini CLI skill (`pos-disambiguator`) for LLM-based POS disambiguation, and detailed linguistic knowledge. Reference it for tagset definitions, disambiguation heuristics, and error patterns.

## Publication Context

- **Paper:** Head-to-head comparison of POS taggers for MHG (models interchangeable, ground truth enables the comparison)
- **DFG network application:** Benchmark serves as demonstrator
- **Edition-matching problem:** Deferred — Michael to assign HiWi for philological review
- **Next meeting:** 7.4.2026

## ReM Data

- **Location:** `ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/` (406 parseable documents, gitignored)
- **Format:** CORA-XML — see [CORA-XML-FORMAT.md](docs/CORA-XML-FORMAT.md)
- **Download:** https://www.linguistics.rub.de/rem/access/index.html (106 MB)
- **Citation:** Roussel, Adam; Klein, Thomas; Dipper, Stefanie; Wegera, Klaus-Peter; Wich-Reif, Claudia (2024). Referenzkorpus Mittelhochdeutsch (1050–1350), Version 2.1. ISLRN 937-948-254-174-0.
- **ReM License:** CC BY-SA 4.0 (benchmark code is CC BY-NC-SA 4.0)

## Commands

```bash
pip install -e ".[dev]"
pytest                          # 101 tests

# Corpus
mhd-bench parse ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ --stats
mhd-bench mapping --validate --corpus-dir ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/

# Evaluate
mhd-bench evaluate corpus/ --adapter passthrough --subset 3
mhd-bench evaluate corpus/ --adapter cli --cli-cmd "claude -p --model opus" --model claude-opus-4.6 --subset 3
mhd-bench evaluate corpus/ --adapter api --provider gemini --model gemini-2.5-pro --api-key --subset 3

# Compare (baselines or cached results)
mhd-bench compare corpus/ --adapters passthrough,majority --subset 3
```

Adapters: `passthrough`, `majority`, `api` (any OpenAI-compatible API), `cli` (any CLI tool)

## Hard Constraints

- **Python 3.13+** with lxml
- **CC BY-NC-SA 4.0** license (benchmark code)
- **ReM data is gitignored** — user downloads separately
- **Tagset mapping YAML** is the single source of truth for HiTS→MHDBDB conversion
- **Technology-agnostic** — adapter interface must support any POS tagger, not just LLMs
- **Docs separation:** `docs/` = promptotyping docs, `docs/guides/` = user-facing guides
- **`.claude/` is gitignored** — user-local settings, not shared

## Documentation

Promptotyping docs: [ARCHITECTURE.md](docs/ARCHITECTURE.md), [REQUIREMENTS.md](docs/REQUIREMENTS.md), [JOURNAL.md](docs/JOURNAL.md)
User guides: [GETTING-STARTED.md](docs/guides/GETTING-STARTED.md), [MODEL-ADAPTER-GUIDE.md](docs/guides/MODEL-ADAPTER-GUIDE.md), [TROUBLESHOOTING.md](docs/guides/TROUBLESHOOTING.md)
All docs → [README.md](README.md)
