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

## 2026-03-16 — save

**Done:** Full Phase 1 MVP: repo scaffold, CORA-XML parser, tagset mapper, gold passthrough adapter, evaluation engine, report generator, CLI, 23 tests. YAML mapping validated against full ReM corpus (0 unmapped tags). Promptotyping docs distilled (HITS-TAGSET.md, TAGSET-MAPPING.md, journal.md). All docs verified against web sources.
**Decisions:** Suffix system A/S/D/N confirmed by Katharina. DGA→DET, DGS→PRO, DPOSD→POS, PTKANT→INJ, KO*→null (exclude Phase 1), PAVW→ADV (not IPA). ReM citation added. Benchmark license CC BY-NC-SA 4.0 (intentional, ReM itself is CC BY-SA 4.0).
**Dead ends:** Initial YAML draft based on HiTS publication had 32 unmapped tags — real ReM uses suffix system not fully documented in Dipper et al. 2013.
