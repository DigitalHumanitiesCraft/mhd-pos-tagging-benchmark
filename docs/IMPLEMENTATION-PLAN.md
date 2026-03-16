# Implementation Plan (Historical)

Original plan from session 2026-03-16. Phase 1 is implemented — see [ARCHITECTURE.md](ARCHITECTURE.md) for current state.

## Origin

Created during context export from `mhdbdb-tei-only` sibling project. Team meeting 9.3.2026 agreed on ReM as ground truth, standalone benchmark repo, model-agnostic adapter interface.

## Phase 1 — MVP (DONE)

Parser, mapper, evaluator, CLI, tests. All 10 steps completed. See [JOURNAL.md](JOURNAL.md) for decisions made during implementation.

## Phase 2 — Model Evaluation (OPEN)

See [REQUIREMENTS.md](REQUIREMENTS.md) for full user stories (E2, E3, E4).

Key items:
- Adapter implementations (LLM APIs, encoder models, classical taggers)
- Result caching (JSONL per document+model+version)
- `mhd-bench compare` command for multi-model comparison
- LaTeX report output for paper
- Per-genre and per-difficulty breakdowns
- Error pattern analysis (top confused tag pairs)

## Known Challenges

1. **VA* → VEX overcount:** Documented limitation, affects all models equally.
2. **Tokenization for LLMs:** Adapters receive pre-tokenized forms, must return one tag per token.
3. **Genre metadata:** ReM may not consistently encode genre. May need manual CSV.
4. **LLM API costs:** Full corpus × multiple models. Mitigated by caching + subset evaluation.
