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
mhd-bench mapping --validate

# Run pipeline sanity check (gold passthrough = 100% accuracy)
mhd-bench evaluate --adapter passthrough
```

## Data

Download ReM v2.1 CORA-XML from [the official site](https://www.linguistics.rub.de/rem/access/index.html) and extract into the repo root. The data is gitignored.

## Documentation

| Document | Content |
|----------|---------|
| [MHDBDB-TAGSET.md](docs/MHDBDB-TAGSET.md) | Target 19-tag tagset with functional distinctions |
| [CORA-XML-FORMAT.md](docs/CORA-XML-FORMAT.md) | ReM data format reference |
| [OVERLAP-TABLE.md](docs/OVERLAP-TABLE.md) | ReM ↔ MHDBDB text overlap mapping |
| [IMPLEMENTATION-PLAN.md](docs/IMPLEMENTATION-PLAN.md) | Full implementation plan |

## License

CC BY-NC-SA 4.0
