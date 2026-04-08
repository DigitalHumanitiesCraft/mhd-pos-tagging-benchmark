# Requirements — MHD POS Tagging Benchmark

## Research Question

**Which model tags Middle High German POS best?** Direct head-to-head comparison against validated ground truth (ReM). Models and technologies are interchangeable — the benchmark works for frontier LLMs (e.g., Gemini 3.1 Pro, Claude Opus 4.6), open-source LLMs, encoder models, classical taggers. What makes the comparison possible at all is the ground truth pipeline (ReM → HiTS → MHDBDB).

Secondary use: demonstrator for DFG network application.

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
| E1.3 | As a developer, I want a gold passthrough adapter that returns mapped ground truth, so that I can verify the pipeline produces 100% accuracy | Must | Done (validated on full corpus: 100% accuracy, 2,122,630 tokens, 16 tags) |
| E1.4 | As a researcher, I want per-tag P/R/F1 and confusion matrices, so that I can identify which tags a model struggles with | Must | Done |
| E1.5 | As a researcher, I want a CLI that combines parse → map → evaluate → report, so that I can run the benchmark in one command | Must | Done |

### E2: Model Evaluation (Phase 2) — Next

Plug in **any** POS tagger — LLM, encoder model, classical — via the adapter interface.

| ID | User Story | Priority | Status |
|----|-----------|----------|--------|
| E2.1 | As a researcher, I want to plug in any POS tagger via a simple adapter interface (input: tokens, output: tags), so that the benchmark is fully technology-agnostic — LLMs, encoder models (BERT-style), fine-tuned classifiers, CRF/HMM, anything | Must | Done (adapter ABC + 4 adapters: passthrough, majority, generic API, generic CLI). E5 delivers universal access. |
| E2.2 | As a researcher, I want to evaluate at least one frontier LLM (Gemini or Claude), so that I can measure generative model performance on MHG POS | Must | Ready (Gemini API + Claude CLI adapters built, not yet run on full corpus) |
| E2.3 | As a researcher, I want to evaluate at least one open-source/self-trained model, so that the paper has a non-commercial baseline | Must | Open |
| E2.4 | As a researcher, I want result caching (JSONL per document+model+version), so that I don't re-run expensive evaluations | Must | Done (config hash, length validation, corrupt-line recovery) |
| E2.5 | As a researcher, I want `mhd-bench compare` to show a side-by-side table of multiple models, so that I can quickly see which model wins on which tags | Should | Done |
| E2.6 | As a researcher, I want a configurable prompt template for LLM-based adapters (derived from MHDBDB pos-disambiguator skill), so that LLMs get comparable instructions | Should | Done (shared prompt_template.py with MHG-specific system prompt) |

### E5: Universal Model Access (Phase 2)

Make the "technology-agnostic" claim real. A user who clones the repo should be able to benchmark **any** LLM — via API key, via CLI subscription, or via custom code — without modifying the benchmark source.

Three access paths:

```
                        ┌─────────────────────────┐
                        │   ModelAdapter (ABC)     │
                        │   .predict(doc) → tags   │
                        └────────┬────────────────┘
               ┌─────────────────┼──────────────────┐
               ▼                 ▼                    ▼
    ┌──────────────────┐ ┌───────────────┐ ┌──────────────────┐
    │ OpenAI-compat API│ │ Generic CLI   │ │ Custom adapter   │
    │ --adapter openai │ │ --adapter cli │ │ (user writes     │
    │ --model gpt-4o   │ │ --cli-cmd ... │ │  Python class)   │
    │ --base-url ...   │ │               │ │                  │
    └──────────────────┘ └───────────────┘ └──────────────────┘
    OpenAI, Mistral,     Claude Code,       BERT, CRF, HMM,
    Anthropic, Ollama,   Codex CLI,         fine-tuned models,
    vLLM, LiteLLM,      Vibe CLI,          anything with
    any /v1/chat/        Gemini CLI,        Python bindings
    completions endpoint any stdin→stdout
```

| ID | User Story | Priority | Status |
|----|-----------|----------|--------|
| E5.1 | As a researcher with an API key (OpenAI, Mistral, Gemini, Groq, or any OpenAI-compatible endpoint), I want to benchmark my model with `--adapter api --provider NAME --model MODEL --api-key KEY`, so that I don't need to write code or understand the adapter interface | Must | Done (GenericApiAdapter, openai SDK, provider presets for openai/gemini/mistral/groq) |
| E5.2 | As a researcher with a CLI subscription (Claude, Gemini, Codex, Copilot, Vibe, or any CLI that reads stdin and writes stdout), I want to benchmark my tool with `--adapter cli --preset NAME --model MODEL`, so that I can use any CLI-based LLM without writing an adapter | Must | Done (GenericCliAdapter with presets: claude, gemini, codex, copilot + `--cli-cmd` fallback for unknown CLIs) |
| E5.3 | As a developer with a custom model (fine-tuned BERT, CRF, HMM, or any model with Python bindings), I want a documented adapter interface with a working example, so that I can write a `ModelAdapter` subclass and plug it in without reading the full codebase | Must | Done (MODEL-ADAPTER-GUIDE.md with 3 examples: dictionary, BERT, CRF + runner script + checklist) |
| E5.4 | As a researcher, I want `--api-base` support for the API adapter, so that I can point it at Ollama (`localhost:11434`), vLLM, LiteLLM, or any self-hosted endpoint | Should | Done (--api-base flag, auto-detects local endpoints and skips API key requirement) |
| E5.5 | As a researcher, I want the shared MHG system prompt and response parsing used by all LLM adapters (API and CLI), so that prompt differences don't confound model comparison | Must | Done (prompt_template.py shared by all LLM adapters — API and CLI presets) |
| E5.6 | As a researcher, I want `--adapter api --provider NAME` to work with just an env var (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`, etc.) and no `--api-base` for the big providers, so that the common case is zero-config | Should | Done (provider presets in GenericApiAdapter with env var names + default base URLs) |

**Acceptance criteria (verified):**

```bash
# API key users — zero-code, works out of the box
mhd-bench evaluate corpus/ --adapter api --provider openai --model gpt-4o --api-key sk-...
mhd-bench evaluate corpus/ --adapter api --provider gemini --model gemini-2.5-pro --api-key AI...
mhd-bench evaluate corpus/ --adapter api --provider mistral --model devstral --api-key ...
mhd-bench evaluate corpus/ --adapter api --api-base http://localhost:11434/v1 --model llama3

# CLI subscription users — zero-code, works out of the box
mhd-bench evaluate corpus/ --adapter cli --cli-cmd "claude -p --model opus" --model claude-opus-4.6
mhd-bench evaluate corpus/ --adapter cli --cli-cmd "gemini -m gemini-3.1-pro-preview -p" --model gemini-3.1-pro-preview
mhd-bench evaluate corpus/ --adapter cli --cli-cmd "codex exec" --model codex

# Custom model users — implement ModelAdapter in Python
# (interface documented in ARCHITECTURE.md with example)
```

**Design notes:**
- `GenericApiAdapter` wraps the OpenAI Python SDK (`openai>=1.0`), which supports any `/v1/chat/completions` endpoint via `base_url`. Provider presets (openai, gemini, mistral, groq) handle base URLs and env var names automatically.
- `GenericCliAdapter` sends prompt via stdin (avoids argument-length limits on Windows), appends empty string to `-p`/`--prompt` flags. System prompt embedded in user prompt with task-first structure (for agentic CLIs).
- Custom adapters implement `ModelAdapter.predict(document) → list[str]`.
- All paths share `prompt_template.py` (system prompt + response parsing + tag validation).
- CLI presets know per-tool specifics: system prompt delivery (flag vs embed), prompt delivery (stdin vs argument), response format (raw vs JSON key), extra flags. Users can override or extend presets via `cli-profiles.yaml` (same schema as built-ins).

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
| E4.1 | As a developer, I want `pytest` with >90% coverage on core modules, so that refactoring is safe | Should | Partial (130 tests, coverage not measured) |
| E4.2 | As a developer, I want JSON result output, so that results are machine-readable for downstream analysis | Must | Done |
| E4.3 | As a researcher, I want the benchmark to handle the full ReM corpus (2.5M tokens) in under 5 minutes for the passthrough adapter | Should | Not benchmarked |
| E4.4 | As a developer, I want a MODEL-ADAPTER-GUIDE.md, so that contributors can plug in new models without reading all the code | ~~Could~~ Must | Open → moved to E5.3 (upgraded to Must) |

## Success Criteria

### Minimum Viable Benchmark (for paper submission)

1. Gold passthrough produces **100% accuracy** on full corpus (pipeline validation)
2. At least **3 models evaluated** across technology categories: e.g., 1 frontier LLM, 1 open-source LLM, 1 encoder/classical tagger
3. Per-tag P/R/F1 table with all 16 mapped MHDBDB tags (IPA/CNJ/DIG have 0 support — documented)
4. Confusion matrix showing systematic error patterns
5. Exclusion rate and reasons documented (currently 17.7%: punctuation, untagged, FM, KO*)
6. Known limitations section: VA*→VEX overcount, no IPA mapping, KO* excluded
7. **A user can clone the repo and benchmark any LLM** (via API key, CLI subscription, or custom adapter) without modifying benchmark source code (E5)

### Stretch Goals

- Per-genre analysis (Vers vs. Prosa)
- Overlap subset analysis (ReM ∩ MHDBDB)
- \>5 models compared
- Context-sensitive KO* resolution
- Adapter auto-discovery via setuptools entry points (register custom adapters without editing cli.py)

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
