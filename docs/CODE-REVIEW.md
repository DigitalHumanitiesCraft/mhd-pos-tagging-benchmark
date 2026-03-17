# MHD POS Tagging Benchmark — Code & Project Report

**Date:** 2026-03-17
**Reviewer:** Claude Opus 4.6 (automated code review, two-pass analysis)
**Scope:** Full codebase — every `.py`, `.yaml`, `.xml` fixture, config, test, and doc

---

## Executive Summary

A well-structured research benchmark at Phase 1 complete / Phase 2 in progress. The architecture is clean, the pipeline is sound, and all 39 tests pass. The code is internally consistent about the 16 evaluable MHDBDB tags — but documentation says "19" everywhere. The most impactful real bugs are in the CLI adapter layer (hardcoded model, unretried `KeyError`), a Windows encoding gap, and a cache that doesn't track what it cached. 9 of 15 modules have zero test coverage. 7 files from Phase 2 work remain uncommitted.

**Errata from first-pass review:** The initial automated review (prior to this version) incorrectly flagged two "crash-level bugs" in `subset.py` — an alleged infinite loop and a ZeroDivisionError. Both were false positives upon careful code tracing. They have been removed and replaced with the actual (lower-severity) subset issues. The `VALID_TAGS` concern has been reclassified from HIGH to documentation-only — the code is correct for Phase 1.

---

## 1. HIGH-SEVERITY BUGS

### 1.1 `claude_cli.py` hardcodes `--model sonnet`, ignores `model_name`

**File:** `src/mhd_pos_benchmark/adapters/claude_cli.py:42`

```python
"--model", "sonnet",  # ← hardcoded, ignores self._model_name
```

The `model_name` parameter controls only the cache key and adapter name. A caller passing `model_name="claude-opus"` gets Sonnet responses cached under the label "claude-opus". This produces silently wrong benchmark results.

**Action:** Use a separate `cli_model` parameter (or derive from `model_name`) to set the `--model` flag.

### 1.2 `_extract_text` KeyError bypasses retry logic

**File:** `src/mhd_pos_benchmark/adapters/claude_cli.py:47-48` + `cli_base.py:137`

```python
# claude_cli.py
def _extract_text(self, stdout, stderr):
    data = json.loads(stdout)
    return data["result"]  # ← KeyError if "result" missing
```

The retry handler in `_call_cli` catches `(ValueError, RuntimeError)` but not `KeyError`. If Claude Code returns valid JSON without a `"result"` key (e.g., an error envelope), the adapter crashes immediately with no retry — unlike every other failure mode which gets 3 attempts.

**Action:** Catch `KeyError` in the retry block, or wrap `_extract_text` in a try/except that converts `KeyError` to `ValueError`.

### 1.3 Missing `encoding="utf-8"` on file operations (Windows)

**Files:** `mapping/tagset_mapper.py:18`, `evaluation/report.py:84`, `cli.py:317`

```python
with open(yaml_path) as f:       # tagset_mapper — reads YAML with MHG examples
with open(path, "w") as f:       # report.py — writes JSON with ensure_ascii=False
with open(output, "w") as f:     # cli.py compare — writes comparison JSON
```

On Windows (this environment), `open()` defaults to `cp1252`, not UTF-8. The YAML contains MHG terms in comments, and JSON output contains MHG word forms with diacritics. With `ensure_ascii=False`, non-ASCII characters go straight to the file, producing mojibake or `UnicodeEncodeError` on Windows.

**Action:** Add `encoding="utf-8"` to all three `open()` calls. The `cache.py` already does this correctly — follow that pattern.

### 1.4 Cache ignores configuration — stale results across runs

**File:** `adapters/cache.py`

The cache key is `(adapter_name, document_id)`. It does not track:
- **chunk_size** — changing from 200 to 100 returns cached 200-chunk results
- **prompt version** — editing the system prompt returns old-prompt results
- **model version** — if Sonnet updates, cached results persist
- **mapping version** — if the YAML changes (altering `mappable_tokens`), cached predictions have the wrong count

No length validation on cache retrieval: `cli_base.py:69-72` and `gemini.py:60-63` return cached `list[str]` without checking `len(cached) == len(document.mappable_tokens)`.

**Action:** Store a metadata hash (chunk_size + prompt hash + mapping version) in the JSONL entry. Validate prediction count on retrieval.

---

## 2. MEDIUM-SEVERITY ISSUES

### 2.1 Form mismatch in error analysis output

**File:** `evaluation/comparator.py:49`

```python
AlignedPair(
    form=token.form_modernized,  # ← report shows "rîter"
    ...
)
```

But all LLM adapters send `token.form_diplomatic` (e.g., "ritter") as input. When reviewing errors, researchers see the modernized form in the report while the LLM saw a different (diplomatic) form. This makes error diagnosis harder — you can't tell if the LLM misread the input.

**Action:** Add `form_diplomatic` to `AlignedPair` alongside `form_modernized`, or switch to diplomatic as the primary display form.

### 2.2 Context loss at chunk boundaries degrades accuracy

**File:** `adapters/prompt_template.py:120-126`

Each chunk restarts word numbering from 1 with no overlap and no surrounding context. For context-dependent tags — which the system prompt itself highlights as "Critical Distinctions" (DET vs. SCNJ for "daz", VRB vs. VEX for auxiliary verbs) — a token at the start of a chunk loses all left context.

Example: "daz" at position 201 (start of chunk 2) — the LLM can't see whether it follows a noun (→ DET) or introduces a verb-final clause (→ SCNJ).

**Action:** Implement the `overlap` parameter (currently reserved but unused) to provide N tokens of context on each side of a chunk. Even 10-20 tokens of overlap would significantly reduce boundary errors.

### 2.3 System prompt example contradicts actual prompt format

**File:** `adapters/prompt_template.py:54-55` vs `:106`

The system prompt shows unnumbered input: `Input: sô sprach der rîter`
But `build_tagging_prompt` sends numbered input: `1. sô\n2. sprach\n3. der\n4. rîter`

This mismatch may confuse LLMs. The few-shot example teaches one format; the actual task uses another.

**Action:** Update the system prompt example to use the numbered format, or remove numbering from the prompt.

### 2.4 Cache corrupt-line handling

**File:** `adapters/cache.py:28`

```python
entry = json.loads(line)  # ← no try/except
```

A single corrupt JSONL line (from a crash during `put()`) crashes the entire `_load()`, making all cached results inaccessible.

**Action:** Wrap in `try/except json.JSONDecodeError` with a warning log, skipping corrupt lines.

### 2.5 `tagset_mapper.map_token()` silently swallows unknown tags

**File:** `mapping/tagset_mapper.py:43-44`

```python
except KeyError:
    token.pos_mhdbdb = None  # ← indistinguishable from FM, $_, --, KO*
```

Unknown HiTS tags (typos, new tags from a future ReM version) are silently treated as "unmappable" — the same as deliberately excluded tags. No warning is emitted. The `find_unmapped()` method exists to detect this, but it's never called automatically during `map_document()`.

**Action:** Add `logger.warning("Unknown HiTS tag: %r in token %s", ...)` inside the except block.

### 2.6 `Gemini response.text` can be `None`

**File:** `adapters/gemini.py:111`

If Gemini's safety filter blocks a response, `response.text` is `None`. Passing `None` to `parse_tag_response()` causes `AttributeError: 'NoneType' object has no attribute 'strip'`.

**Action:** Check `if response.text is None: raise ValueError("Gemini response blocked by safety filter")` before parsing.

### 2.7 No error handling around `adapter.predict()` in comparator

**File:** `evaluation/comparator.py:38`

A single API failure aborts the entire `align_corpus()` with no partial results. For 407 documents with LLM adapters over hours of evaluation, this means starting over.

**Action:** Add per-document try/except with error logging and optional `--continue-on-error` mode.

### 2.8 Parser silently drops tokens without `<pos>` element

**File:** `data/rem_parser.py:73-78`

Tokens without a `<pos>` child or with an empty `pos tag=""` are silently skipped — no count, no log. For a benchmark claiming 2.58M tokens, undocumented token loss is a data integrity risk.

**Action:** Count and log skipped tokens, at least at DEBUG level.

### 2.9 `subset.py` can return fewer documents than requested

**File:** `data/subset.py:42-68`

Two independent mechanisms cause under-allocation:
1. **Rounding**: `round(n * len(docs) / len(documents))` can produce a total < n with no upward-adjustment loop (only a downward trim loop exists).
2. **Middle-third selection**: For small genres (e.g., 6 documents), `middle = docs[2:4]` is only 2 items. If `count=3`, `rng.sample(middle, min(3, 2))` returns 2, silently losing a document.

The function returns fewer than `n` with no warning. `describe_subset()` will show the actual count, but the caller doesn't know documents were lost.

**Action:** Add a warning log when `len(selected) < n`, and consider falling back to non-middle documents to fill the gap.

### 2.10 No protection against evaluating before mapping

**Files:** `adapters/gold_passthrough.py:20`, `evaluation/comparator.py:50`

If `map_document()` was never called, all tokens have `pos_mhdbdb = None`, so `mappable_tokens` is empty. `GoldPassthroughAdapter.predict()` returns `[]`, `align_document` produces 0 pairs, and `compute_metrics` raises `"No evaluated tokens"`. The error message doesn't mention the actual cause (missing mapping step).

This is easy to trigger: call `mhd-bench evaluate` with a custom adapter that receives unmapped documents.

**Action:** Either verify `any(t.pos_mhdbdb is not None for t in doc.tokens)` in the comparator, or make `_parse_and_map` the only entry point to the pipeline.

---

## 3. LOW-SEVERITY / CODE QUALITY ISSUES

| # | Issue | File:Line | Description |
|---|-------|-----------|-------------|
| 3.1 | Dead variable | `subset.py:38` | `remaining = n` assigned, never read |
| 3.2 | Falsy zero | `cli.py:30` | `if subset:` is False for `subset=0`; should be `if subset is not None:` |
| 3.3 | Redundant metric | `metrics.py` | `micro_f1` = accuracy for single-label classification. Redundant but not wrong. |
| 3.4 | No confusion matrix in console | `report.py` | Computed and serialized in JSON, but `print_report()` never displays it |
| 3.5 | Labels from data only | `metrics.py:69` | Tags absent from subset are omitted; should pass canonical 16-tag set for consistent cross-run reporting |
| 3.6 | Shadow import | `metrics.py:81` | Loop variable `f1` shadows the imported `f1_score` function |
| 3.7 | Sort mismatch | `report.py` | Console: per-tag sorted by support (descending). JSON: alphabetical. |
| 3.8 | No `@cached_property` | `corpus.py:36-43` | `mappable_tokens` / `excluded_tokens` rebuild list on every call. Used in sort lambdas (O(n·k·log n)). |
| 3.9 | `setuptools-scm` unused | `pyproject.toml:2` | In build-requires but version is hardcoded as `"0.1.0"` |
| 3.10 | Mixed line endings | git warnings | LF vs CRLF across modified files |
| 3.11 | Unused parameter | `cli.py:40` | `_resolve_api_key(api_key, adapter_name)` — `adapter_name` is accepted but never used |
| 3.12 | Untyped parameter | `cli.py:47` | `_make_adapter(name, documents, ...)` — `documents` has no type annotation |
| 3.13 | Test CWD pollution | `tests/test_cli_adapters.py:292` | `test_name` and `test_availability_check_fails` create `results/claude-cli/` in CWD (no `tmp_path`) |
| 3.14 | Duplicate cache entries | `cache.py:41` | `put()` appends without dedup. JSONL grows unboundedly. Last-line-wins on reload is correct but wasteful. |
| 3.15 | No parallel evaluation | `comparator.py:68` | `align_corpus` processes documents sequentially. For LLM adapters, this means hours with no concurrency. |
| 3.16 | No per-document breakdown | `report.py` | Cannot identify which documents cause the most errors from the report output |
| 3.17 | `compare` JSON sparse | `cli.py:304-315` | Compare output omits per-tag metrics, confusion matrices, exclusion stats. Can't do detailed post-hoc analysis. |
| 3.18 | YAML `ambiguous_mappings` unused | `hits_to_mhdbdb.yaml:148` | Loaded by `safe_load` but never read by `TagsetMapper`. Dead configuration data. |

---

## 4. DOCUMENTATION INCONSISTENCIES

| Claim | Location | Reality |
|-------|----------|---------|
| "19 MHDBDB POS tags" | YAML:3, CLAUDE.md, MHDBDB-TAGSET.md, README.md | **16** unique non-null target tags in the YAML. CNJ, IPA, DIG have no HiTS source. Code and tests are correct at 16 — `test_all_16_mapped_mhdbdb_tags_present` explicitly verifies this. Docs are wrong. |
| "407 files" | CLAUDE.md | 406 parseable documents (confirmed by YAML:18 and `parse_corpus` output) |
| "Gemini 3.1 Pro" | CLAUDE.md, RESEARCH.md | `gemini.py:31` defaults to `gemini-2.5-pro` |
| "Claude Opus 4.6" | CLAUDE.md | `claude_cli.py:42` hardcodes `--model sonnet` |
| `mhd-bench evaluate --adapter passthrough` | README.md Quick Start | Missing required `CORPUS_DIR` positional arg — this command errors |
| "Target 19-tag tagset" | README.md doc table | Should say "16 evaluable tags (3 reserved for Phase 2)" |

### Why this matters for the paper

The "19 vs 16" discrepancy will create confusion in peer review. The MHDBDB tagset definition (MHDBDB-TAGSET.md) lists 19 tags. The benchmark evaluates 16. The paper must clearly state: *"Of the 19 MHDBDB tags, 3 (IPA, CNJ, DIG) have no corresponding HiTS source tag and are excluded from evaluation."* The code is correct; the documentation needs to catch up.

---

## 5. MULTI-MOD TOKENS: DESIGN DECISION, NOT BUG

**File:** `data/rem_parser.py:68-69`

First-pass review flagged this as a bug. On second analysis: for multi-mod tokens like "inder" → "in" + "der", the parser gives all sub-tokens the full diplomatic form "inder" because there's only one `<tok_dipl>` for the whole token. The sub-token modernized forms ("in", "der") are correct.

Since LLM adapters use `form_diplomatic`, the LLM sees "inder" for both sub-tokens. This is **technically correct** — the manuscript literally reads "inder". The LLM should tag based on what was actually written. The modernized split ("in" + "der") exists for linguistic analysis, not for reading the source.

**Recommendation:** Document this behavior. If you want LLMs to tag individual morphemes, switch to `form_modernized` as the input form. But for diplomatic-form benchmarking, the current behavior is defensible.

---

## 6. TEST COVERAGE

### Current state: 39 tests, all passing

| Module | Tests | Notes |
|--------|-------|-------|
| `data/rem_parser.py` | 6 | Happy path only. No `parse_corpus()`, no malformed XML, no missing `<pos>`. |
| `mapping/tagset_mapper.py` | 12 | Good. Covers mappings, suffix system, unmappable, unknown. Missing `map_document()`, `find_unmapped()`. |
| `evaluation/metrics.py` | 4 | Basic. No per-tag value checks, no multi-document aggregation, no `exclusion_rate`. |
| `adapters/prompt_template.py` | 6 (via test_cli_adapters) | `parse_tag_response` well tested. `build_tagging_prompt` and `build_chunked_prompts` untested. |
| `adapters/claude_cli.py` | 10 | Good coverage of predict, retry, cache, chunking. Missing: `_extract_text` error paths. |

### Untested modules (9 of 15)

| Module | Risk | Why it matters |
|--------|------|----------------|
| `data/subset.py` | Medium | Under-allocation and edge cases in proportional selection |
| `adapters/cache.py` | **High** | Corrupt-line crash, duplicate handling, stale-data retrieval |
| `evaluation/comparator.py` | **High** | Core glue; prediction-count mismatch `ValueError` untested |
| `evaluation/report.py` | Medium | JSON encoding on Windows, save_json correctness |
| `adapters/gold_passthrough.py` | Medium | Pipeline sanity check — the one adapter that *must* produce 100% |
| `adapters/majority_class.py` | Medium | Empty corpus `ValueError`, `most_common` correctness |
| `adapters/gemini.py` | Low | API adapter, would need mock; similar patterns to tested `claude_cli` |
| `data/corpus.py` | Low | Simple dataclasses, but `is_mappable` / `mappable_tokens` untested |
| `cli.py` | Low | Click CLI; could use `CliRunner` for smoke tests |

### Missing test scenarios in existing test files

- `test_rem_parser`: No test for `parse_corpus()` (directory parsing), malformed XML, missing `<pos>`, empty `pos tag=""`, tokens without `<tok_dipl>`
- `test_tagset_mapper`: No test for `map_document()`, `find_unmapped()`, or that `map_token()` silently swallows unknown tags (the current `test_unknown_tag_raises` only tests `map_tag`)
- `test_metrics`: No test for `per_tag` P/R/F1 values, `exclusion_rate` property, multi-document aggregation, or the `"No evaluated tokens"` ValueError
- `test_cli_adapters`: `test_name` and `test_availability_check_fails` create `results/claude-cli/` in CWD (should use `tmp_path`)

---

## 7. UNCOMMITTED WORK

3 untracked + 4 modified files representing Phase 2 CLI adapter work:

| File | Status | Lines changed |
|------|--------|---------------|
| `adapters/claude_cli.py` | **New** (untracked) | Claude CLI adapter |
| `adapters/cli_base.py` | **New** (untracked) | Shared CLI adapter base class |
| `tests/test_cli_adapters.py` | **New** (untracked) | 16 tests for CLI adapters |
| `adapters/gemini.py` | Modified | Refactored to use shared `prompt_template` (-45/+0 net) |
| `adapters/prompt_template.py` | Modified | Extracted shared prompt/parsing logic (+44 lines) |
| `cli.py` | Modified | Added `compare` command + claude-cli adapter choice (+53 lines) |
| `data/subset.py` | Modified | Genre-stratified subset selection (+13 lines) |

**Action:** Commit this work to avoid accidental loss. It's a coherent Phase 2 unit.

---

## 8. ARCHITECTURAL OBSERVATIONS

### What's done well

- **Clean separation of concerns**: parser → mapper → adapter → comparator → metrics → report. Each module has a single job.
- **Technology-agnostic adapter interface**: `ModelAdapter` ABC is minimal and correct. Adding a new tagger requires only `name` + `predict()`.
- **YAML as single source of truth**: One file governs all tag mapping. Changes propagate automatically.
- **Cache design**: JSONL per adapter is simple and works. `ResultCache` is cleanly encapsulated.
- **Test quality where tests exist**: The `test_cli_adapters.py` tests are well-structured with proper mocking and isolation.

### What needs attention for the paper

1. **Reproducibility**: The cache doesn't record what parameters produced a result. A reviewer running the benchmark with different chunk_size would get stale cached results.
2. **Error analysis**: The report doesn't show *which* tags get confused most. For the paper, you need "top-10 confused tag pairs from the confusion matrix." This requires post-processing the JSON output.
3. **Per-genre analysis**: The subset selector exists, but there's no built-in way to evaluate per-genre accuracy (Vers vs. Prosa). The paper's "Future Work" mentions this.
4. **VA* → VEX overcount**: This known limitation (documented in YAML:104-105) inflates VEX metrics. The paper should quantify the impact — how many VA* tokens are copular "sîn" (should be VRB) vs. true auxiliaries?

---

## 9. CONCRETE ACTION ITEMS (Priority Order)

### Must Fix (before any evaluation runs)

| # | Action | File(s) | Effort |
|---|--------|---------|--------|
| 1 | Add `encoding="utf-8"` to all `open()` calls | `tagset_mapper.py:18`, `report.py:84`, `cli.py:317` | 5 min |
| 2 | Fix hardcoded `--model sonnet` — use configurable parameter | `claude_cli.py:42` | 10 min |
| 3 | Catch `KeyError` in `_call_cli` retry block | `cli_base.py:137` or `claude_cli.py:47` | 5 min |
| 4 | Commit the 7 uncommitted Phase 2 files | git | 2 min |

### Should Fix (before paper submission)

| # | Action | File(s) | Effort |
|---|--------|---------|--------|
| 5 | Correct all "19 tags" → "16 evaluable tags" in docs | CLAUDE.md, YAML:3, README, MHDBDB-TAGSET.md | 15 min |
| 6 | Fix README Quick Start — add `CORPUS_DIR` argument | README.md:20 | 2 min |
| 7 | Correct model names in docs (gemini-2.5-pro, sonnet, 406 docs) | CLAUDE.md, RESEARCH.md | 5 min |
| 8 | Add cache length validation on retrieval | `cli_base.py:69`, `gemini.py:60` | 10 min |
| 9 | Add `json.JSONDecodeError` handling in `cache._load()` | `cache.py:28` | 5 min |
| 10 | Guard `response.text is None` in Gemini adapter | `gemini.py:111` | 5 min |
| 11 | Add `logger.warning` for unknown tags in `map_token()` | `tagset_mapper.py:43` | 5 min |
| 12 | Fix system prompt example to match numbered format | `prompt_template.py:54` | 5 min |
| 13 | Warn when subset returns fewer than n documents | `subset.py:68` | 5 min |
| 14 | Add per-document `try/except` in `align_corpus` | `comparator.py:68` | 15 min |

### Should Add (test coverage)

| # | Action | Priority |
|---|--------|----------|
| 15 | Tests for `cache.py` — corrupt lines, duplicates, stale retrieval | **High** |
| 16 | Tests for `comparator.py` — length mismatch, error handling | **High** |
| 17 | Tests for `subset.py` — edge cases, under-allocation | Medium |
| 18 | Tests for `report.py` — JSON encoding on Windows | Medium |
| 19 | Tests for `gold_passthrough.py` — must produce 100% accuracy | Medium |
| 20 | Integration test: parse → map → gold passthrough → metrics = 100% | Medium |
| 21 | Fix `test_name` / `test_availability_check_fails` to use `tmp_path` | Low |

### Nice to Have

| # | Action |
|---|--------|
| 22 | Implement chunk overlap for context-dependent tags |
| 23 | Use `@cached_property` for `mappable_tokens` / `excluded_tokens` |
| 24 | Pass canonical 16-tag label set to sklearn for consistent reporting |
| 25 | Add confusion matrix display to `print_report()` |
| 26 | Add top-N confused tag pairs to report (for paper) |
| 27 | Add `.env` to `.gitignore` |
| 28 | Add `form_diplomatic` to `AlignedPair` for error analysis |
| 29 | Consider relaxing `requires-python` from 3.13+ to 3.11+ |
| 30 | Add `[tool.ruff.lint]` rule selection to `pyproject.toml` |
