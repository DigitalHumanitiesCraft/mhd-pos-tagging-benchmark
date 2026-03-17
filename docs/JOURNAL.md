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
