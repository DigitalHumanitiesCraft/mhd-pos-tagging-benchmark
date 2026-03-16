# MHD POS Tagging Benchmark

Model-agnostic benchmark for Part-of-Speech tagging of Middle High German texts.

Uses the [ReM (Referenzkorpus Mittelhochdeutsch)](https://www.linguistics.rub.de/rem/) as ground truth with hand-annotated HiTS POS tags. Evaluates any POS tagger via a pluggable adapter interface. Reports accuracy, per-tag precision/recall/F1, and confusion matrices.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Parse ReM data and show statistics
mhd-bench parse ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ --stats

# Validate tagset mapping against actual data
mhd-bench mapping --validate --corpus-dir ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/

# Run pipeline sanity check (gold passthrough = 100% accuracy)
mhd-bench evaluate --adapter passthrough
```

## Data

Download ReM v2.1 CORA-XML from [the official site](https://www.linguistics.rub.de/rem/access/index.html) and extract into the repo root. The data is gitignored.

## Documentation

| Document | Content |
|----------|---------|
| [MHDBDB-TAGSET.md](docs/MHDBDB-TAGSET.md) | Target 19-tag tagset with functional distinctions |
| [HITS-TAGSET.md](docs/HITS-TAGSET.md) | Source HiTS tagset — all 73 tags with corpus frequencies |
| [TAGSET-MAPPING.md](docs/TAGSET-MAPPING.md) | HiTS → MHDBDB mapping rationale and gap analysis |
| [CORA-XML-FORMAT.md](docs/CORA-XML-FORMAT.md) | ReM data format reference |
| [OVERLAP-TABLE.md](docs/OVERLAP-TABLE.md) | ReM ↔ MHDBDB text overlap mapping |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Pipeline, data model, adapter interface, modules |
| [REQUIREMENTS.md](docs/REQUIREMENTS.md) | User stories, epics, success criteria |
| [RESEARCH.md](docs/RESEARCH.md) | Academic context, related work, research gap |
| [IMPLEMENTATION-PLAN.md](docs/IMPLEMENTATION-PLAN.md) | Historical plan (Phase 2 items) |
| [JOURNAL.md](docs/JOURNAL.md) | Decision log and process journal |

## License

CC BY-NC-SA 4.0
