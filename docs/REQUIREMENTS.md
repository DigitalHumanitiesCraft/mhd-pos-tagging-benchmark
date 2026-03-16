# Requirements — MHD POS Tagging Benchmark

## Project Goal

Systematically evaluate POS taggers for Middle High German against ReM ground truth. Serve as infrastructure for a publication comparing Frontier LLMs vs. open-source/self-trained models. Secondary use: demonstrator for DFG network application.

## Stakeholders

| Who | Needs | Validates |
|-----|-------|-----------|
| **Michael** (professor, TU Darmstadt) | Publishable results, paper narrative | Linguistic plausibility, methodology |
| **Christian** (tech lead, DHCraft) | Reliable tooling, reproducible runs | Pipeline correctness, code quality |
| **Katharina** (MHDBDB lead, Salzburg) | MHDBDB tagset accuracy, correct mapping, corpus handling | Mapping decisions, ReM-specific edge cases |
| **Paper reviewers** | Transparent methodology, reproducibility | Metrics, corpus description, limitations section |

## Epics

### E1: Ground Truth Pipeline (Phase 1) — DONE

Parse ReM CORA-XML → map HiTS to MHDBDB → evaluate → report.

| ID | User Story | Priority | Status |
|----|-----------|----------|--------|
| E1.1 | As a researcher, I want to parse all ReM CORA-XML files into a structured format, so that I can access tokens with their POS tags programmatically | Must | Done |
| E1.2 | As a researcher, I want every HiTS tag in the corpus mapped to an MHDBDB tag (or explicitly excluded), so that no tokens silently fall through | Must | Done (73/73 mapped) |
| E1.3 | As a developer, I want a gold passthrough adapter that returns mapped ground truth, so that I can verify the pipeline produces 100% accuracy | Must | Done (not yet run on full corpus) |
| E1.4 | As a researcher, I want per-tag P/R/F1 and confusion matrices, so that I can identify which tags a model struggles with | Must | Done |
| E1.5 | As a researcher, I want a CLI that combines parse → map → evaluate → report, so that I can run the benchmark in one command | Must | Done |

### E2: Model Evaluation (Phase 2) — Next

Plug in **any** POS tagger — LLM, encoder model, classical — via the adapter interface.

| ID | User Story | Priority | Status |
|----|-----------|----------|--------|
| E2.1 | As a researcher, I want to plug in any POS tagger via a simple adapter interface (input: tokens, output: tags), so that the benchmark is fully technology-agnostic — LLMs, encoder models (BERT-style), fine-tuned classifiers, CRF/HMM, anything | Must | Open |
| E2.2 | As a researcher, I want to evaluate at least one frontier LLM (Gemini or Claude), so that I can measure generative model performance on MHG POS | Must | Open |
| E2.3 | As a researcher, I want to evaluate at least one open-source/self-trained model, so that the paper has a non-commercial baseline | Must | Open |
| E2.4 | As a researcher, I want result caching (JSONL per document+model+version), so that I don't re-run expensive evaluations | Must | Open |
| E2.5 | As a researcher, I want `mhd-bench compare` to show a side-by-side table of multiple models, so that I can quickly see which model wins on which tags | Should | Open |
| E2.6 | As a researcher, I want a configurable prompt template for LLM-based adapters (derived from MHDBDB pos-disambiguator skill), so that LLMs get comparable instructions | Should | Open (LLM-specific, not all adapters) |

### E3: Analysis & Publication (Phase 2–3)

Deeper analysis for the paper.

| ID | User Story | Priority | Status |
|----|-----------|----------|--------|
| E3.1 | As a researcher, I want per-genre accuracy breakdowns (Vers vs. Prosa), so that I can discuss genre effects in the paper | Should | Open |
| E3.2 | As a researcher, I want error pattern analysis (top confused tag pairs per model), so that I can characterize failure modes | Should | Open |
| E3.3 | As a researcher, I want LaTeX table output for metrics, so that I can paste results directly into the paper | Should | Open |
| E3.4 | As a researcher, I want to evaluate on the ~25 overlap texts (ReM ∩ MHDBDB) separately, so that I can compare MHDBDB's own tags against ReM ground truth | Could | Open — blocked by edition matching |
| E3.5 | As a researcher, I want per-difficulty breakdowns (e.g., ambiguous tags like DET/PRO), so that I can discuss where models struggle most | Could | Open |

### E4: Infrastructure & Quality

| ID | User Story | Priority | Status |
|----|-----------|----------|--------|
| E4.1 | As a developer, I want `pytest` with >90% coverage on core modules, so that refactoring is safe | Should | Partial (23 tests, coverage not measured) |
| E4.2 | As a developer, I want JSON result output, so that results are machine-readable for downstream analysis | Must | Done |
| E4.3 | As a researcher, I want the benchmark to handle the full ReM corpus (2.5M tokens) in under 5 minutes for the passthrough adapter | Should | Not benchmarked |
| E4.4 | As a developer, I want a MODEL-ADAPTER-GUIDE.md, so that contributors can plug in new models without reading all the code | Could | Open |

## Success Criteria

### Minimum Viable Benchmark (for paper submission)

1. Gold passthrough produces **100% accuracy** on full corpus (pipeline validation)
2. At least **3 models evaluated** across technology categories: e.g., 1 frontier LLM, 1 open-source LLM, 1 encoder/classical tagger
3. Per-tag P/R/F1 table with all 16 mapped MHDBDB tags (IPA/CNJ/DIG have 0 support — documented)
4. Confusion matrix showing systematic error patterns
5. Exclusion rate and reasons documented (currently 17.7%: punctuation, untagged, FM, KO*)
6. Known limitations section: VA*→VEX overcount, no IPA mapping, KO* excluded

### Stretch Goals

- Per-genre analysis (Vers vs. Prosa)
- Overlap subset analysis (ReM ∩ MHDBDB)
- >5 models compared
- Context-sensitive KO* resolution

## Known Constraints

| Constraint | Impact | Mitigation |
|-----------|--------|------------|
| ReM data is gitignored (106 MB) | Reviewers can't reproduce without downloading | Document download instructions, provide sample fixture |
| VA*→VEX overcounts auxiliary | Inflates VEX, undercounts VRB for copula | Document as limitation, affects all models equally |
| No IPA/CNJ/DIG in mapping | 3 of 19 tags show 0 support | Document; these are rare or structural |
| KO* excluded (22k tokens) | 0.9% of corpus not evaluated | Phase 2 context-sensitive resolver |
| Edition mismatch ReM↔MHDBDB | Overlap subset comparison may be noisy | Deferred — Michael assigns HiWi for philological review |
| LLM API costs | Full corpus × multiple models = expensive | Caching (E2.5), possibly subset evaluation first |
| Genre imbalance in overlap | Epic-heavy, minimal lyric | Report genre distribution, caveat in paper |
