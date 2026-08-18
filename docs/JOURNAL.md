# Journal — MHD POS Tagging Benchmark

## 2026-03-16 — Initial build + corpus validation

### Decisions
- Repo scaffold built: pyproject.toml, CLI, parser, mapper, evaluator, tests (17/17 pass)
- Parser uses `<tok_anno>` + `<pos>` (instance-level) as per CLAUDE.md decisions
- Multi-mod tokens (clitics) → one Token per `<tok_anno>` element
- Gold passthrough adapter validates pipeline (should produce 100% accuracy)

### Corpus Scan Results
- **406 documents** parsed (407 in dir, 1 apparently skipped or empty)
- **2,579,276 tokens** total (tok_anno elements with POS)
- **73 unique HiTS tags** in actual corpus data

### Critical Finding: YAML Draft vs. Real Tags

The draft YAML mapping was based on HiTS documentation (Dipper et al. 2013). The actual ReM v2.1 annotations use a **suffix system** not fully described in the publication:

| Suffix | Meaning | Example |
|--------|---------|---------|
| `A` | attributiv (modifies noun) | `DDA`, `DIA`, `DPOSA`, `CARDA` |
| `S` | substituierend (replaces noun) | `DDS`, `DIS`, `DPOSS`, `CARDS` |
| `D` | adverbial | `DDD`, `DID`, `DPOSD`, `CARDD` |
| `N` | nominalisiert | `DDN`, `DIN`, `DPOSN`, `CARDN` |

**32 tags unmapped**, covering **~500k tokens** (~20% of corpus). See TAGSET-MAPPING.md for full gap analysis.

Additionally found:
- `$_` (286k occurrences) — undocumented punctuation variant, not in YAML
- `KO*` (22k) — ambiguous conjunction marker (asterisk = unresolved)
- `AVD-KO*` (503) — comparative demonstrative adverb, asterisk variant
- `DRELS` (26k) — relative determiner/pronoun, substituierend
- `PAV*` (33k total) — pronominal adverbs (PAVD, PAVAP, PAVW, PAVG)
- `PTKANT` (349) — answer particle (ja, nein)
- `ADJ` (2), `VV` (2) — bare base tags (annotation errors or edge cases)

### Open Questions for Katharina
1. Suffix-System: Ist `A`=attributiv, `S`=substituierend, `D`=adverbial, `N`=nominalisiert korrekt?
2. `DRELS` — immer PRO (Relativpronomen ist substituierend), oder gibt es attributive Relative?
3. `PAV*` — alles ADV? Oder PAVW → IPA (interrogativ)?
4. `KO*` — was bedeutet der Asterisk? Ambig zwischen KON/KOUS?
5. `$_` — welche Interpunktion? Abgrenzen von `$.` / `$,`?
6. `PTKANT` — nach MHDBDB-Tagset: INJ? ADV? Eigene Kategorie fehlt.

### Status
- **Pipeline:** funktionsfähig, Tests pass, CLI works
- **Blocker:** YAML-Mapping muss auf echte Tags aktualisiert werden (warten auf Katharina)
- **Next:** HITS-TAGSET.md, TAGSET-MAPPING.md distillen, dann Mapping fixen

## 2026-03-16 — Mapping decisions: DRELS, PAV*

### Confirmed by Christian (nach Korpusbeispiel-Review)
- `DRELS → PRO` — Relativpronomen sind immer substituierend, alle Formen dër-Paradigma
- `PAVD → ADV` — demonstrative Pronominaladverbien (dâr+Präp: darzuo, dâmite)
- `PAVAP → ADV` — präpositionale Pronominaladverbien (Präp+dâr: zuo/dâr+, mite/dâr+)
- `PAVG → ADV` — generalisierte Pronominaladverbien (swâr+Präp)
- `PAVW → ADV` (nicht IPA!) — interrogative Pronominaladverbien (warumbe, warzuo)

### Linguistische Begründung für PAVW → ADV
IPA im MHDBDB-Tagset ist für Partikeln gedacht, die eine Frage einleiten, nicht für lexikalische Frageadverbien. Formen wie warumbe/warzuo sind kompositionell (wâr + Präposition) und syntaktisch Adverbien.

### Distillation completed
- `docs/journal.md` — angelegt
- `docs/HITS-TAGSET.md` — alle 73 Tags mit Frequenzen aus echtem Korpus
- `docs/TAGSET-MAPPING.md` — vollständige Gap-Analyse, 7 Fragen für Katharina
- `docs/CORA-XML-FORMAT.md` — Suffix-System ergänzt

### Still open
- Q2 (DG vs DPOS), Q4 (KO*), Q5 (PTKANT), Q7 (DPOSD) — need Katharina
- DD/DI suffix mappings (DDA, DDS, etc.) — proposed but not yet confirmed
- YAML not yet updated — waiting for remaining decisions

## 2026-03-16 — Katharina's confirmations + YAML rewrite

### Suffix system confirmed
A=attributiv, S=substituierend, D=adverbial, N=nominalisiert. Katharina consulted multiple LLMs and finds the system reasonable.

### All mappings confirmed
| Tag(s) | → MHDBDB | Decision |
|--------|----------|----------|
| DGA | DET | Generalized (swelch-), attributiv |
| DGS | PRO | Generalized (swelch-), substituierend |
| DPOSD | POS | Stays POS even when adverbial |
| PTKANT | INJ | Answer particle (jâ, nein) |
| KO* | null | Context-dependent (SCNJ/CCNJ/ADV), excluded Phase 1 |
| DD* suffix | A→DET, S→PRO, D→ADV, N→PRO | Follows suffix system |
| DI* suffix | A→DET, S→PRO, D→ADV, N→PRO | Follows suffix system |
| DW* suffix | A→DET, S→PRO, D→ADV | Follows suffix system |
| CARD* suffix | All→NUM | Function doesn't change word class |
| PAV* | All→ADV | Already confirmed earlier |
| DRELS | PRO | Already confirmed earlier |

### YAML rewritten (v0.2.0)
- All 73 corpus tags now mapped
- **0 unmapped tags** against full corpus
- Corpus coverage: 2,122,630 mappable (82.3%) / 456,646 excluded (17.7%)
- Excluded: $_ (286k), -- (122k), KO* (22k), FM (26k)
- Removed ~30 stale tags from HiTS documentation that don't appear in ReM v2.1
- Tests updated: 23/23 pass

### Verify results (web search)
- ReM URL, HiTS citation, institutional affiliations: all verified
- **License correction found:** ReM is CC BY-SA 4.0 (not NC). Benchmark code stays CC BY-NC-SA 4.0 (intentional).
- ReM citation added to docs: Roussel et al. (2024), ISLRN 937-948-254-174-0
- HiTS defines 84 tags total, 73 appear in ReM v2.1

### Status
- **Mapping:** COMPLETE — all 73 tags mapped, validated
- **Pipeline:** ready for gold passthrough evaluation
- **Next:** run `mhd-bench evaluate --adapter passthrough` on full corpus (should be 100%)

## 2026-03-16 — save (1)

**Done:** Full Phase 1 MVP: repo scaffold, CORA-XML parser, tagset mapper, gold passthrough adapter, evaluation engine, report generator, CLI, 23 tests. YAML mapping validated against full ReM corpus (0 unmapped tags). Promptotyping docs distilled. All docs verified against web sources.
**Decisions:** Suffix system A/S/D/N confirmed by Katharina. DGA→DET, DGS→PRO, DPOSD→POS, PTKANT→INJ, KO*→null (exclude Phase 1), PAVW→ADV (not IPA). ReM citation added. Benchmark license CC BY-NC-SA 4.0 (intentional, ReM itself is CC BY-SA 4.0).
**Dead ends:** Initial YAML draft based on HiTS publication had 32 unmapped tags — real ReM uses suffix system not fully documented in Dipper et al. 2013.

## 2026-03-16 — save (2)

**Done:** Context compression (IMPLEMENTATION-PLAN 277→30, TAGSET-MAPPING 169→107, CLAUDE.md 81→50). New docs: ARCHITECTURE.md, REQUIREMENTS.md, RESEARCH.md. All docs UPPERCASE. README updated.
**Decisions:** Benchmark fully technology-agnostic (not just LLMs). IMPLEMENTATION-PLAN demoted to historical reference. Three paper framing options identified, deferred.
**Dead ends:** None.

## 2026-03-16 — handoff

**Summary:** Built complete Phase 1 MVP from scratch in one session. CORA-XML parser, HiTS→MHDBDB mapper (73 tags, 2.58M tokens, 0 unmapped), evaluation engine, CLI, 23 tests. Full Promptotyping doc suite (11 docs) distilled, compressed, verified against web sources. Research question sharpened: "Which model tags MHG POS best?" — head-to-head comparison enabled by ground truth, models interchangeable. Repo public at https://github.com/DigitalHumanitiesCraft/mhd-pos-tagging-benchmark.

**Phase:** Implementation (Phase 1 done, Phase 2 ready). 11 docs, all current:
- Knowledge: MHDBDB-TAGSET, HITS-TAGSET, CORA-XML-FORMAT, OVERLAP-TABLE
- Architecture: ARCHITECTURE.md (pipeline, data model, adapter interface)
- Requirements: REQUIREMENTS.md (4 epics, success criteria)
- Research: RESEARCH.md (related work, gap, paper framing)
- Mapping: TAGSET-MAPPING.md + hits_to_mhdbdb.yaml v0.2.0
- Process: JOURNAL.md, IMPLEMENTATION-PLAN.md (historical)

**Open issues:**
- Gold passthrough not yet run on full corpus (should produce 100%)
- KO* (22k tokens) excluded — Phase 2 needs Verbstellung-Heuristik for context-sensitive resolution
- Inter-annotator consistency in ReM not checked (different `annotation_by` values)
- LLM input format undecided: `form_diplomatic` vs. `form_modernized`
- RESEARCH.md citations from web search, not verified against original papers
- GHisBERT (Beck & Köllner 2023) usability for MHG POS not confirmed
- Team roles corrected (Katharina=MHDBDB lead/Salzburg, Michael=professor/TU Darmstadt) — verify with team

**Next steps:**
1. Run `mhd-bench evaluate` with passthrough on full corpus — must be 100%
2. Small subset test on overlap texts (2026-03-17 geplant)
3. Build first real adapter
4. Decide diplomatic vs. modernized forms for LLM input
5. Verify RESEARCH.md citations before paper writing
6. Add GitHub contributors: `michaelscho` (Michael) and `wachauer` (Katharina) to repo

**Git:** 6 commits on main, last `170ef57`, pushed to origin.

## 2026-03-17 — handoff

**Summary:** Phase 2 infrastructure built. Gold passthrough validated (100% accuracy, 2,122,630 tokens, 16 tags). Added majority-class baseline (18.4% — NOM is most frequent tag), Gemini API adapter with MHG-specific prompt template (derived from MHDBDB pos-disambiguator skill), result caching (JSONL), subset selector (genre-stratified), CLI `compare` command, and `--subset` flag. Decided: diplomatic forms as default LLM input (modernized would introduce unvalidated normalization). Planned CLI-subscription adapters (claude -p, gemini CLI) for flat-rate users.

**Phase:** Implementation (Phase 2 in progress). New files this session:
- Adapters: `majority_class.py`, `gemini.py`, `prompt_template.py`, `cache.py`
- Data: `subset.py` (genre-stratified subset selector)
- CLI: updated with `compare` command, `--subset`, `--verbose` flags
- Plan: `docs/CLI-ADAPTER-PLAN.md` (CLI-subscription adapter design)
- Docs from Phase 1 unchanged, still current

**Open issues:**
- GEMINI_API_KEY not set in Christian's environment — Gemini adapter not yet test-run
- CLI-subscription adapters (claude-cli, gemini-cli) designed but not yet implemented — see `docs/CLI-ADAPTER-PLAN.md`
- Gemini CLI exact flags unknown (unlike Claude Code's well-documented `-p` mode)
- Tests not yet written for new adapters (majority, gemini, cache, subset)
- ARCHITECTURE.md not yet updated with new adapter types and CLI changes
- KO* (22k tokens) still excluded — context-sensitive resolution deferred
- Inter-annotator consistency in ReM still unchecked
- RESEARCH.md citations still unverified against original papers
- GitHub contributors (michaelscho, wachauer) still not invited

**Next steps:**
1. Set `GEMINI_API_KEY` and test-run Gemini adapter on subset (`--adapter gemini --subset 10`)
2. Implement CLI-subscription adapters per `docs/CLI-ADAPTER-PLAN.md` — start with `claude-cli`
3. Write tests for new adapters (`test_cli_adapters.py`, `test_majority.py`)
4. Update ARCHITECTURE.md with Phase 2 additions
5. First real head-to-head: `mhd-bench compare ... --adapters majority,gemini --subset 10`
6. Install `google-genai`: `pip install "mhd-pos-benchmark[gemini]"`

**Git:** 7 commits on main, last `8a9cccf`, pushed to origin.

## 2026-03-17 — save

**Done:** Claude CLI adapter implemented and smoke-tested (correct tags on 3 MHG tokens via `claude -p --model opus`). Full CODE-REVIEW.md analysis performed and all 30 issues fixed: 4 high-severity bugs (hardcoded model, KeyError bypass, UTF-8 encoding, cache staleness), 10 medium issues (form mismatch, corrupt cache, missing warnings, error handling), 6 low-severity cleanups, documentation corrections (19→16 evaluable tags, model names, README Quick Start). Shared `parse_tag_response()` extracted to `prompt_template.py`. `--api-key` flag added (masked interactive prompt, never stored). Cache upgraded with config hash + length validation. ARCHITECTURE.md and REQUIREMENTS.md updated.
**Decisions:** Default models: Claude Opus 4.6 (`--model opus`), Gemini 3.1 Pro (`gemini-3.1-pro`). API keys via env var or `--api-key` flag with masked input — no web interface needed. System prompt example updated to numbered format matching actual prompts.
**Dead ends:** Windows cp1252 encoding broke MHG Unicode in subprocess stdin — fixed with `encoding="utf-8"`. Initial 120s timeout too short for 200-token chunks — bumped to 300s.

## 2026-03-17 — handoff

**Summary:** Built Claude CLI adapter (`claude -p --model opus`), shared prompt/parsing infrastructure, and `--api-key` flag with masked interactive input. Performed full code review (CODE-REVIEW.md) and fixed all 30 issues across 4 severity levels. Updated ARCHITECTURE.md and REQUIREMENTS.md. 39 tests pass, pipeline smoke-tested end-to-end with real Claude CLI call on MHG tokens.

**Phase:** Implementation (Phase 2 in progress). All docs current:
- Knowledge: MHDBDB-TAGSET, HITS-TAGSET, CORA-XML-FORMAT, OVERLAP-TABLE
- Architecture: ARCHITECTURE.md (updated with all Phase 2 modules)
- Requirements: REQUIREMENTS.md (E2.1 done, E2.2 ready, E2.4-E2.6 done)
- Research: RESEARCH.md (unchanged, still current)
- Mapping: TAGSET-MAPPING.md + hits_to_mhdbdb.yaml v0.2.0
- Process: JOURNAL.md, CODE-REVIEW.md (new), CLI-ADAPTER-PLAN.md
- Tests: 39 tests across 4 test files

**Open issues:**
- No actual benchmark numbers yet — no model evaluated beyond 3-token smoke test
- Gemini 3.1 Pro model ID (`gemini-3.1-pro`) not verified against Google SDK — may need `models/gemini-3.1-pro` or similar
- GEMINI_API_KEY still not set in Christian's environment
- Chunk boundary accuracy loss not quantified — `overlap` parameter exists but unused
- No encoder/classical adapter (E2.3) — paper needs at least 3 model categories
- KO* (22k tokens) still excluded — context-sensitive resolution deferred
- Inter-annotator consistency in ReM still unchecked
- RESEARCH.md citations still unverified against original papers
- GitHub contributors (michaelscho, wachauer) still not invited
- `results/claude-cli/` has stale cache from smoke test — delete before real runs

**Next steps:**
1. Run first real evaluation: `mhd-bench evaluate ... --adapter claude-cli --subset 10` (expect ~30 min)
2. Delete stale cache: `rm -rf results/claude-cli/`
3. Set GEMINI_API_KEY, test Gemini adapter on subset
4. First head-to-head: `mhd-bench compare ... --adapters majority,claude-cli --subset 10`
5. Investigate encoder model options for E2.3 (GHisBERT? custom fine-tune?)
6. Push to origin: `git push`

**Git:** 8 commits on main, last `480180b`, 1 ahead of origin.

## 2026-03-18 — Session: code review, adapter consolidation, smoke tests

**Done:**
- Full code review (2 iterations from colleague) — fixed 16 issues total, added 62 tests (39→101)
- Adapter consolidation: removed `cli_base.py`, `claude_cli.py`, `gemini.py` → replaced with 2 generic adapters (`generic_api.py`, `generic_cli.py`). Net -324 LOC.
- GenericCliAdapter: prompt via stdin (fixes Windows argument-length limit), `-p`/`--prompt` flag detection, `shutil.which()` path resolution
- GenericApiAdapter: openai SDK, provider presets (openai, gemini, mistral, groq), local endpoint support (ollama/vLLM)
- Smoke test: Claude Opus 4.6 vs Gemini 2.5 Pro vs Gemini 3.1 Pro Preview on M084L (13 tokens). Gemini 3.1 Pro: 100%, Opus + Gemini 2.5: 92.3% (beide `wan` SCNJ→CCNJ)
- MODEL-ADAPTER-GUIDE.md (E5.3): 3 copy-paste examples (dictionary, BERT, CRF)
- README rewritten with real CLI examples and actual output
- E5 (Universal Model Access): all 6 stories Done
- Docs reorganized: `docs/guides/` for user-facing, `docs/` for promptotyping

**Decisions:**
- `--adapter api` + `--adapter cli` replace all model-specific adapters — fully generic
- Gemini CLI model name: `gemini-3.1-pro-preview` (not `gemini-3.1-pro`)
- Prompt via stdin for generic CLI (not as argument) — agentic CLIs interpret long arguments as session setup
- Task-first prompt structure for CLI adapter: user task first, system prompt as REFERENCE after

**Open issues:**
- `compare` command can't compare two different LLMs in one call (global `--cli-cmd`/`--model`) — documented limitation, user does separate evaluate runs
- RESEARCH.md citations still unverified against original papers
- No encoder/classical model evaluated yet (E2.3)
- Prompt-Bias: system prompt contains MHG hints (`wan` → SCNJ) — could confound model comparison
- Reproduzierbarkeit: CLI-Adapter haben keine Temperature-Kontrolle — Paper muss Non-Determinismus diskutieren
- GitHub contributors (michaelscho, wachauer) still not invited

## 2026-03-19 — TODO: UX für Linguist_innen ohne Programmierkenntnisse

**Kernfrage:** Wie können wir es Linguist_innen ohne Programmierkenntnisse ermöglichen, den Benchmark zu nutzen? Aktuell erfordert der Benchmark: Python 3.13 installieren, pip install, CLI-Kommandos, API-Keys setzen. Das ist für Computerlinguist_innen machbar, aber nicht für Mediävist_innen oder Literaturwissenschaftler_innen.

**Mögliche Richtungen (noch nicht entschieden):**
- Web-Interface? (Streamlit, Gradio) — niedrigste Einstiegshürde, aber Hosting nötig
- Docker-Container mit vorkonfiguriertem Setup? — reproduzierbar, aber Docker-Installation nötig
- Google Colab Notebook? — zero-install, aber API-Key-Handling in Colab heikel
- Vereinfachte CLI mit interaktivem Wizard? (`mhd-bench quickstart` → führt durch Setup)
- Vorkonfigurierte Presets? (`mhd-bench evaluate --preset gemini-quick` → setzt alles automatisch)

**Ziel:** Ein/e Forscher/in mit ReM-Zugang und einem LLM-Account (z.B. Gemini, ChatGPT) soll den Benchmark nutzen können, ohne Python-Interna zu verstehen.

## 2026-03-19 — Colleague review iteration 2 + cleanup

**Fixes from iteration 2:**
- Double `from __future__ import annotations` in cache.py — removed
- `compute_metrics` counted empty AlignmentResults in `documents_evaluated` — now filters: `sum(1 for r in results if r.pairs)`
- Retry backoff capped: `min(2 ** attempt, 60)` in both generic_api.py and generic_cli.py (prevents 17-min wait at max_retries=10)
- Subset mismatch communicated to user: CLI prints yellow note when `--subset N` returns fewer than N documents
- `gold_passthrough.py`: added `# type: ignore[misc]` for mypy (mappable_tokens guarantees non-None)
- `majority_class.py`: added docstring note about cheating baseline for paper reviewers

**Also done:**
- GitHub contributors invited: `michaelscho` (Michael) + `wachauer` (Katharina) — both write access
- `.claude/` added to .gitignore (user-local settings)
- CLAUDE.md updated: GitHub usernames, .claude gitignore note, 101 tests

## 2026-03-19 — handoff

**Summary:** Third review iteration from colleague — 6 issues fixed (duplicate import, documents_evaluated count, backoff cap, subset UX, type safety, baseline disclaimer). GitHub contributors invited. CLAUDE.md updated to current state. .claude/ gitignored.

**Phase:** Implementation (Phase 2 in progress). 101 tests, all passing. 13 docs, all current.

**Open issues:**
- E2.3: No open-source/encoder model evaluated yet — paper needs min. 3 model categories
- `compare` command can't compare two different LLMs in one call — documented limitation, user does separate evaluate runs
- RESEARCH.md citations from web search, not verified against original papers
- Prompt-Bias: system prompt contains MHG-specific hints that could confound model comparison
- CLI-Adapter Temperature nicht kontrollierbar → Non-Determinismus im Paper diskutieren
- UX for non-programmers: see TODO 2026-03-19 above (web UI? Colab? wizard?)

**Next steps:**
1. UX exploration for linguists without programming skills (2026-03-19 TODO)
2. E2.3: evaluate one open-source model (e.g. Llama 3 via ollama — infrastructure ready)
3. Larger benchmark run: `--subset 10`+ with Claude + Gemini for statistical significance
4. Verify RESEARCH.md citations against original papers
5. Push to origin

**Git:** main branch, ahead of origin — push pending.

## 2026-03-19 — UX improvements + compare --models + handoff

**Done this session (continued):**
- `compare --models`: CachedAdapter loads predictions from previous evaluate runs. Users can now compare any two models without re-running them. Fixes the core `compare` limitation.
- `mhd-bench doctor`: diagnostic command with auto-detection of Python, corpus, CLI tools, API keys, cache. Generates max 3 copy-paste command suggestions (1 CLI, 1 API, 1 compare).
- Corpus auto-detection: `corpus_dir` optional in all commands. Searches `./corpus/`, `./ReM-v2.1_coraxml/.../cora-xml/`, etc. No more typing the nested path.
- Better error messages: `--adapter gemini` → "Did you mean --adapter api --provider gemini?". Model names as adapter names get "Did you mean" hints. All errors point to `mhd-bench doctor`.
- README simplified: Quick Start uses `doctor`, commands drop corpus path.

**Decisions:**
- No interactive wizard (`quickstart`). `doctor` with command suggestions achieves the same UX without composability/testing/maintenance overhead. Christian's feedback: "quickstart is overengineered — doctor with --suggest does the same thing."
- `suggest_commands()` priority: max 1 CLI (flat-rate, cheapest) + max 1 API (fastest) + 1 compare (if cached). Avoids noise when many tools are available.
- Presets deferred — `doctor` suggestions serve the same purpose without new infrastructure.

## 2026-03-19 18:45 — handoff

**Summary:** Fixed `compare` command limitation (new `--models` flag for cached results), built `mhd-bench doctor` with smart suggestions, added corpus auto-detection to all commands, improved error messages with "Did you mean" hints. 130 tests, all pushed.

**Phase:** Implementation (Phase 2 in progress). 130 tests, 14 docs, all current.

**Open issues:**
- E2.3: No open-source/encoder model evaluated yet — paper needs min. 3 model categories
- RESEARCH.md citations from web search, not verified against original papers
- Prompt-Bias: system prompt contains MHG-specific hints that could confound model comparison
- CLI-Adapter Temperature nicht kontrollierbar → Non-Determinismus im Paper diskutieren
- GETTING-STARTED.md not yet updated with `doctor` recommendation (README done)
- ARCHITECTURE.md not yet updated with doctor.py, cached.py modules

**Next steps:**
1. Update GETTING-STARTED.md to recommend `mhd-bench doctor` as first step
2. Update ARCHITECTURE.md with new modules (doctor.py, cached.py) and 130 test count
3. E2.3: evaluate Llama 3 via ollama (infrastructure ready: `--adapter api --api-base http://localhost:11434/v1`)
4. Larger benchmark run: `--subset 10`+ for statistically meaningful results
5. Verify RESEARCH.md citations against original papers

**Git:** `cd8d497` on main, pushed to origin.

## 2026-03-19 — CLI presets + smoke test results

**Done:**
- CLI presets system: each CLI tool (claude, gemini, codex, copilot) has a preset that knows system prompt delivery (flag vs embed), prompt delivery (stdin vs argument), response format (raw vs json_key), extra flags
- GenericCliAdapter rewritten to use presets — `--preset claude --model opus` replaces `--cli-cmd "claude -p --model opus"`
- cli-profiles.yaml for user-defined CLI profiles (same schema, overrides built-ins)
- --cli-cmd stays as escape hatch for unknown CLIs
- Smoke tested: Claude preset 6/6 on M044 (system prompt via --system-prompt flag, JSON output, stdin delivery)
- Gemini preset correctly configured (argument delivery, --yolo, raw output) but blocked by Google capacity during test — not a code issue
- Large comparison run (subset 10): Gemini completed 8/10 docs (7531 tokens), Claude timed out due to rate limiting when run in parallel. Lesson: run models sequentially, not in parallel

**Decisions:**
- CLI presets over per-CLI adapter files. One GenericCliAdapter with preset config instead of separate ClaudeCliAdapter, GeminiCliAdapter, etc.
- stdin delivery for Claude (supports it natively), argument delivery for Gemini (requires -p VALUE)
- YAML profiles use same schema as built-in presets — no learning curve for users extending

**Known issues from comparison run:**
- Gemini 2.5 Pro occasionally returns wrong tag count (199 instead of 200) on large chunks — retries usually fix it
- Claude CLI subprocess very slow when run in parallel with other Claude processes (rate limiting)
- Both models struggle with M345 and M408 (12k+ tokens each, 60+ chunks) — needs investigation whether smaller chunk_size helps

## 2026-03-19 — First benchmark result + handoff

**Summary:** First real benchmark result: Gemini 3.1 Pro Preview scores 90.08% accuracy on 8 docs / 7,531 tokens (zero-shot, no MHG training). Claude Opus comparison blocked by rate limiting when run from Claude Code — must be run in separate terminal. CLI presets shipped, docs updated, MODEL-ADAPTER-GUIDE rewritten for non-programmers.

**Phase:** Implementation (iteration). 130 tests, all passing. Docs current.

**First result — Gemini 3.1 Pro Preview (8 docs, 7,531 tokens):**
- Accuracy: 90.08%, Macro-F1: 86.04%
- Strong: NOM (0.952), NAM (0.965), POS (0.964), VEM (0.958), CCNJ (0.957)
- Weak: VEX (0.450 — recall only 29%, copula/auxiliary confusion), ADJ (0.790), INJ (0.667, n=5)
- Cached in results/gemini-3.1-pro-preview/ (8 docs, reusable)

**Critical discovery:** `claude -p` (CLI subprocess) cannot run from within Claude Code — they share the same account/rate limit. Benchmark runs with Claude must happen in a **separate terminal**. This is a fundamental constraint, not a bug.

**Open issues:**
- Claude Opus comparison still missing — run in separate terminal (commands below)
- E2.3: no open-source/encoder model evaluated yet
- VEX F1=0.450 is a known limitation (VA*→VEX overcount in HiTS mapping, affects all models equally)
- Gemini capacity issues with 2.5 Pro intermittent — Flash works reliably
- RESEARCH.md citations not verified against original papers

**Next steps (for next session or separate terminal):**
1. Run Claude comparison in separate terminal:
   ```
   python -m mhd_pos_benchmark.cli evaluate --adapter cli --preset claude --model opus --subset 3 --continue-on-error
   python -m mhd_pos_benchmark.cli compare --models claude-opus-4.6,gemini-3.1-pro-preview --subset 3
   ```
2. E2.3: evaluate Llama 3 via ollama (`--adapter api --api-base http://localhost:11434/v1`)
3. Investigate smaller chunk_size (100 instead of 200) for reliability on large docs
4. Verify RESEARCH.md citations

**Git:** `548392c` on main, pushed to origin.

## 2026-08-18 — Functional test + adaptation to the current model and harness reality

Five months after the last session (last entry 2026-03-19). Everything was tested against the tools as
they exist today, then adapted.

### What still worked

130 tests green, corpus parsing (406 documents), tagset validation, passthrough
evaluation (accuracy 1.0000), `doctor`, and the Claude CLI adapter end to end
(4,7 s for a 10-token probe, plausible tags).

### What had broken

| Finding | Evidence |
|---|---|
| Gemini CLI dead for consumer accounts | `IneligibleTierError: no longer supported for Gemini Code Assist for individuals`, retired 2026-06-18, successor is Antigravity CLI (`agy`) |
| Tagger read the benchmark's own docs | `claude -p` started in the repo answered "ReM v2.1, HiTS 73 tags, MHDBDB 19/16" when asked what the project uses, despite `--system-prompt` |
| 25.782 input tokens of harness overhead per chunk | ~1,6 million tokens per document at `chunk_size=200`, versus 1.814 per chunk when isolated |
| `doctor` suggested a command that crashes | `compare --models a,b` on caches with no shared documents aborts with a traceback |
| Copilot reported as installed | `shutil.which` found the VS Code extension's `copilot.ps1`, which blocks on an interactive install prompt |
| Every model ID outdated | `opus`, `claude-opus-4.6`, `gemini-2.5-pro`, `gpt-4o`, `devstral`, `llama-3.3-70b-versatile` |

### Measurements behind the isolation fix

Probe question the model can only answer from project files, neutral working
directory, Claude Code 2.1.234:

| Invocation | Input tokens | Answer |
|---|---|---|
| as shipped before | 25.782 | describes the project |
| `--tools ""` alone | 31.589 | NO-CONTEXT |
| `--strict-mcp-config` alone | 24.732 | NO-CONTEXT |
| both together | 1.814 | NO-CONTEXT |

MCP server definitions and skills dominate the prompt; the two flags only work
in combination. `--bare` would be the cleanest switch but never reads OAuth
credentials ("Not logged in"), so it is unusable on a subscription login.

Verified after the change, through the shipped preset: 2.602 input tokens,
answer `NO-CONTEXT`, empty working directory.

### Changes

- Presets carry `--tools "" --strict-mcp-config --disable-slash-commands` and a
  new `isolate_cwd` flag; the adapter runs the subprocess in an empty temp dir
- Model IDs pinned and dated: `claude-opus-5`, `gemini-3.1-pro-preview`,
  `gpt-5.6`, `gpt-5.2-codex`, `mistral-large-latest`, `openai/gpt-oss-120b`
- New `antigravity` preset (`agy -p`), unverified, carries a caveat
- Presets that could not be exercised locally carry a `caveat` field that
  `evaluate` prints before the run: antigravity, codex, copilot, and gemini
  (for the tier retirement)
- `doctor` detects editor shims, and only suggests `compare` for caches that
  actually share documents
- Model substitution happens after argument splitting, so names with spaces
  ("Gemini 3.1 Pro (High)") survive
- 144 tests, all passing

### Corrections to earlier entries

The 2026-03-19 entry (First benchmark result) claims `claude -p` cannot run from inside Claude Code
because of a shared rate limit. That no longer holds: every CLI test this
session ran from inside Claude Code without hitting a limit.

### Open issues

- Subset selection and cache have drifted apart: `--subset 8` picks M106, M351,
  M408, while the Gemini cache holds M255, M114, M121S. There is no way to name
  documents explicitly, so cached results become unreachable once selection
  shifts. A `--documents M033,M174,...` flag would fix this and make published
  runs reproducible. Not implemented, needs a decision.
- `chunk_size=200` dates from an era of smaller context windows. With current
  models a larger chunk would cut the per-call overhead further.
- antigravity, codex and copilot presets are unverified.
- Claude comparison against Gemini 3.1 still missing.

## 2026-08-18 — Pinned document selection + chunk size measured

Follow-up to the same session: both open issues from the entry above were taken
on.

### Explicit document selection

`--documents M033,M174,...` selects exactly the named texts, for `evaluate` and
`compare`. Unknown IDs abort the run with a list of what was missing and
near-miss suggestions; skipping them silently would change what a published
number covers.

Three supporting mechanisms, because naming documents only helps if people
notice they should:

- every `--subset` run now prints the `--documents` line that repeats it exactly
- saved JSON results carry `document_ids`
- `compare` warns when models were scored on different documents and prints the
  `--documents` line for the shared set (`coverage_mismatch`)

The March Gemini cache is reachable again: `compare --models
gemini-3.1-pro-preview --documents M033,M174,M040,M255,M226,M021,M114,M121S`
reproduces 90,08 % over all 8 documents and 7.531 tokens, the exact figure from
the 2026-03-19 entry. Through `--subset 8` only 5 of those documents were still
reachable.

### Chunk size: measured, default kept

M021 (1.364 tokens), Claude Opus 5, retries disabled:

| chunk | calls | seconds | accuracy |
|---|---|---|---|
| 200 | 7 | 385,8 | 0,8981 |
| 500 | 3 | 365,1 | 0,8930 |
| 1364 (whole document) | 1 | 363,3 | 0,9135 |

M174 (423 tokens) showed the same direction: 0,9078 at chunk 200 versus 0,9125
in a single call.

Token usage per call, same model: chunk 200 costs 4.582 in / 3.505 out, chunk
500 costs 6.306 in / 10.649 out.

What this changes:

1. **Chunk size is a confounder, not a performance knob.** 1,5 accuracy points
   between the extremes. Models are only comparable at the same chunk size.
   The cache config hash already separates runs; `compare` now warns when
   cached results carry different hashes, which it previously accepted silently
   (`CachedAdapter` loads without hash filtering by design).
2. **Bigger chunks are not cheaper.** They save harness overhead on input but
   provoke much more reasoning on output, and output is the expensive half.
   Over the 8-document set at Opus 5 rates: $4,64 at chunk 200 against $5,36 at
   chunk 500. The premise behind the open issue was wrong.
3. **Wall-clock is flat**, so there is no speed argument either.

The default stays at 200, which also keeps the existing Gemini cache valid.
`--chunk-size` is now exposed on `evaluate` and `compare` for anyone who wants
to trade cost for the accuracy that longer context buys.

Side effect: per-call time scales with chunk size, so the CLI adapter's timeout
now does too (`max(300, chunk_size * 0.8)`). At chunk 1364 a call took 363 s,
which the previous fixed 300 s would have killed on every attempt.

### State

170 tests, all passing. ruff clean.

### Open issues

- antigravity, codex and copilot presets remain unverified (tools not installed).
- Claude has not yet been run over the 8 cached Gemini documents, so the
  head-to-head is still missing. The command is now unambiguous:
  `mhd-bench evaluate --adapter cli --preset claude --model claude-opus-5
  --documents M033,M174,M040,M255,M226,M021,M114,M121S`
- Whether the accuracy gain from whole-document chunks holds across models is
  untested. If it does, it is a finding for the paper rather than a setting.

## 2026-08-18 — Subscription access for GPT and Gemini

Question that started this: can GPT and Gemini be benchmarked through existing
subscriptions rather than API keys? For the project that matters beyond cost,
because colleagues without an API budget should be able to reproduce a run.

Answer: yes for both, through different tools than before.

### What was installed and what it needs

| Tool | Version | Auth | State |
|---|---|---|---|
| Codex CLI | 0.147.0 | ChatGPT plan login | flags verified, login expired |
| Copilot CLI | 1.0.80 | GitHub Copilot subscription | works end to end |
| Antigravity CLI (`agy`) | 1.1.14 | Google account | installed, login pending |

`~/.codex/auth.json` already held a ChatGPT login (`auth_mode: chatgpt`, no API
key) from 7 April, and `codex login status` reported "Logged in using ChatGPT".
The refresh token turned out to be spent (`refresh_token_reused`), so a fresh
`codex login` is needed. `agy` needs an interactive sign-in as well. Both are
browser flows, so they cannot be done from inside a session.

### Three findings from making the presets actually run

**Codex refuses an untrusted directory.** `isolate_cwd` runs every call in an
empty temp dir, which codex rejects with "Not inside a trusted directory".
`--skip-git-repo-check` fixes it. The isolation and the tool's own safety check
collide, and nothing about that is obvious from either side.

**npm wrappers on Windows truncate long prompts.** Through `copilot.CMD` the
Copilot CLI received only the first line of the tagging prompt and answered with
an echo of it; exit code 0, no error, unusable output. The identical call
through `node npm-loader.js` returned correct tags. cmd.exe mangles a long
multi-line argument passed through a batch wrapper. The adapter now unwraps
`.CMD`/`.BAT` launchers to a direct node call, but only where the prompt goes in
as an argument. This is the kind of failure that would have been read as "the
model can't do it".

**Copilot's `auto` picks the model itself.** It chose Claude Haiku 4.5. A run
labelled "Copilot" would have measured whatever Copilot felt like that day.
Available on this subscription: `claude-sonnet-4.5`, `claude-haiku-4.5`. GPT
names were rejected as unavailable, so GPT goes through codex, not copilot.

Smoke test through the preset: copilot with `claude-sonnet-4.5` tagged the
10-token probe correctly in 13,2 s.

### Also

`resolve_real_executable` now lives in `doctor.py` and is used by both `doctor`
and the CLI adapter, so neither can end up measuring the VS Code Copilot shim
that shadows the real CLI on PATH. `doctor` now reports all five CLIs as
available.

176 tests, all passing.

### Open

- `codex login` and `agy` sign-in, both interactive.
- Once those are done, the head-to-head can cover Claude, GPT and Gemini on the
  8 cached documents at zero marginal cost, all on subscriptions.

## 2026-08-18 — Correction: the model lists were guessed, so they were wrong

Both logins are in place, and that exposed a methodological error in the entry
above. The available models had been established by trying a handful of names
that seemed plausible and recording which ones failed. Two of the resulting
statements were false.

The trigger was Codex's own interface: it offered `gpt-5.6-terra` and
`gpt-5.6-sol`, while the entry above claims only `gpt-5.4` is available. The
earlier probe had tested `gpt-5.6`, `gpt-5.6-codex`, `gpt-5.4-codex` and
`gpt-5.2-codex`, all of which really are rejected, and concluded from four
misses that the family was unavailable. The tested names simply were not the
names the tool uses.

### Where the model lists actually come from

| Tool | Authoritative source |
|---|---|
| Antigravity | `agy models`, live from the account |
| Codex | `~/.codex/models_cache.json`, refreshed by the CLI from the account |
| Copilot | no listing command outside the TUI, so probe name by name |
| Claude | `--model` takes an alias (`opus`, `sonnet`, `fable`) or a full ID |

Codex on this ChatGPT plan (cache stamped 2026-08-18, client 0.147.0), in the
tool's own priority order: `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`,
`gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.3-codex-spark`. Sol, Terra and Luna
share a 272k context (872k maximum) and differ in default reasoning level, which
is a setting rather than part of the ID.

Copilot, probed one name at a time (an invalid name fails in about 3 s on the
flag check, a valid one runs the prompt, so a sweep is cheap): available are
`claude-sonnet-4.6`, `claude-sonnet-4.5`, `claude-haiku-4.5`, `gpt-5.4`,
`gpt-5.3-codex`, `gpt-5-mini`, `gemini-3.1-pro-preview`, `gemini-3.5-flash`.
Rejected: every `claude-opus` spelling, `gpt-5.6`, `gpt-5.5`, `gpt-4.1`,
`gemini-3-pro`, `gemini-3.1-pro`. So the claim "Copilot has Claude but no GPT"
was wrong in both directions: GPT-5.4 is there, Opus is not.

Antigravity, from `agy models`: `gemini-3.7-flash-{high,medium,low}`,
`gemini-3.6-flash-{high,medium,low}`, `gemini-3.5-flash-{high,medium,low}`,
`gemini-3.1-pro-{high,low}`, `claude-sonnet-4-6`, `claude-opus-4-6-thinking`,
`gpt-oss-120b-medium`. Pro ships high and low but no medium.

### Consequences

Preset defaults are now `gpt-5.6-sol` for codex and `claude-sonnet-4.6` for
copilot, replacing `gpt-5.4` and the unreproducible `auto`. Both were smoke
tested through the adapter on the 10-token probe and returned the expected tags:
codex in 5,7 s, copilot in 7,5 s.

Two things worth carrying into the paper:

- `gemini-3.1-pro-preview` is reachable through Copilot, which is the same model
  name as the March API run at 90,08 %. That is a free replication of an
  API-priced result, and a direct test of whether the harness moves the number.
- Claude Sonnet 4.6 is reachable through Copilot and through Antigravity. Same
  model, two harnesses: if the scores differ, the benchmark is measuring the
  harness, so the route belongs in the results table beside the model name.

The general lesson is cheap to state and was expensive to learn: a model name
that fails proves nothing about a model that exists. Read the list from the
tool, and re-read it before a publication run.

## 2026-08-18 — handoff

**Summary:** Five months of drift caught up with in one session. The benchmark
was tested against the tools as they exist today, then adapted: harness
isolation for the CLI presets, pinned document selection, chunk size measured as
a confounder, four subscription paths for Claude, GPT and Gemini verified end to
end, and the model IDs for every CLI read from the tools themselves after a
first round of guessed names produced two false findings. 176 tests green, ruff
clean, nothing benchmarked beyond 10-token probes.

**Phase:** Implementation. Infrastructure is ready for the head-to-head; no
comparative numbers were produced today.

### What changed

- **Harness isolation.** Presets carry `--tools "" --strict-mcp-config
  --disable-slash-commands` and run in an empty temp directory. Without both
  flags a `claude -p` call started in this repo read CLAUDE.md and could answer
  questions about the benchmark's own ground truth, at 25.782 instead of 1.814
  input tokens per chunk. Contamination and a factor of 14 in cost, both gone.
- **`--documents M033,M174,...`** for `evaluate` and `compare`, plus the
  supporting machinery: `--subset` prints the equivalent pinned line, saved JSON
  carries `document_ids`, `compare` warns when models were scored on different
  texts, and `doctor` only suggests comparisons over documents the caches share.
- **`--chunk-size`** exposed, and measured on M021: 0,8981 at chunk 200 against
  0,9135 in a single 1364-token call. Chunk size is a confounder, not a knob,
  and bigger chunks are not cheaper either (more reasoning output).
- **Four subscription routes verified**, no API key needed: `claude` with
  `claude-opus-5`, `codex` with `gpt-5.6-sol`, `antigravity` with
  `gemini-3.1-pro-high`, `copilot` with `claude-sonnet-4.6`. All four returned
  identical correct tags on the 10-token probe.
- **Model IDs read from the tools**, not guessed. Full per-tool lists and their
  sources are in ARCHITECTURE.md and in the correction entry above.
- **Two silent-failure fixes:** npm `.CMD` wrappers on Windows truncate a long
  multi-line prompt argument, so the adapter unwraps them to a direct node call;
  and the VS Code Copilot shim that shadows the real CLI on PATH is now skipped
  by `resolve_real_executable`.

### Open issues

- **No head-to-head yet.** The March Gemini result (90,08 % over 8 documents) is
  still the only real number. Claude covers 1 of those 8 documents. The run is
  prepared and costs nothing beyond quota:
  `mhd-bench evaluate corpus/ --adapter cli --preset <p> --model <m>
  --documents M033,M174,M040,M255,M226,M021,M114,M121S`
- **Route as a variable.** Claude Sonnet 4.6 is reachable via Copilot and via
  Antigravity, Gemini 3.1 Pro Preview via Copilot and via the Gemini API. Worth
  one deliberate comparison before publishing, because a difference there is the
  harness, not the model.
- **Chunk size across models** is untested. If the whole-document gain holds for
  every model, it is a finding for the paper rather than a setting.
- Gemini CLI stays consumer-dead since 2026-06-18 (`IneligibleTierError`).
- Older items unchanged: KO* still excluded, inter-annotator consistency in ReM
  unchecked, RESEARCH.md citations unverified, edition matching deferred to
  Michael's HiWi.

### Next steps

1. Run the four subscription models on the 8 pinned documents, same
   `--chunk-size`, and record the route beside each model name.
2. Compare, and check whether the Gemini API number replicates through Copilot.
3. Only then touch the paper table.

**Git:** committed and pushed to main on 2026-08-18.
