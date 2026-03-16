# HiTS → MHDBDB Tagset Mapping

Maps 73 HiTS POS tags (ReM v2.1) to 16 MHDBDB POS tags + null. The YAML file at `src/mhd_pos_benchmark/mapping/hits_to_mhdbdb.yaml` is the single source of truth for code.

**Related:** [HITS-TAGSET.md](HITS-TAGSET.md) (source tags with frequencies) · [MHDBDB-TAGSET.md](MHDBDB-TAGSET.md) (target tags with functional distinctions)

**Status:** VALIDATED — all 73 corpus tags mapped. 0 unmapped. Confirmed by Katharina 2026-03-16.
Coverage: 2,122,630 mappable (82.3%) / 456,646 excluded (17.7%) of 2,579,276 total tokens.

## Mapping Principles

1. **Suffix system:** A=attributiv→DET, S=substituierend→PRO, D=adverbial→ADV, N=nominalisiert→PRO. Exception: DPOS* always → POS.
2. **Default for ambiguous:** Phase 1 uses static defaults. Context-sensitive resolution deferred to Phase 2.
3. **`null` = excluded:** Punctuation, foreign material, untagged, ambiguous (KO*) → not evaluated.
4. **Document known overcounts:** VA* → VEX overcounts because HiTS doesn't distinguish copula from auxiliary.

## Complete Mapping Table

| HiTS | → MHDBDB | Count | Rationale |
|------|----------|------:|-----------|
| **Nouns** | | | |
| `NA` | NOM | 387,767 | Common noun |
| `NE` | NAM | 52,593 | Proper noun |
| **Adjectives** | | | |
| `ADJA` | ADJ | 61,846 | Attributive |
| `ADJD` | ADJ | 29,626 | Predicative/adverbial |
| `ADJS` | ADJ | 14,989 | Other |
| `ADJN` | ADJ | 5,392 | Nominalized (default ADJ; could be NOM) |
| `ADJ` | ADJ | 2 | Annotation artifact |
| **Adverbs** | | | |
| `AVD` | ADV | 159,727 | Demonstrative (dâ, hie, sô) |
| `AVW` | ADV | 5,211 | Interrogative (default ADV; could be IPA) |
| `AVG` | ADV | 2,811 | General |
| **Demonstratives (DD)** | | | |
| `DDART` | DET | 149,086 | Article (der, diu, daz) |
| `DDA` | DET | 13,383 | Attributiv |
| `DDS` | PRO | 46,155 | Substituierend |
| `DDD` | ADV | 1,036 | Adverbial |
| `DDN` | PRO | 287 | Nominalisiert |
| **Indefinites (DI)** | | | |
| `DIA` | DET | 29,766 | Attributiv |
| `DIART` | DET | 20,382 | Article (ein) |
| `DIS` | PRO | 7,181 | Substituierend |
| `DID` | ADV | 2,034 | Adverbial |
| `DIN` | PRO | 1,299 | Nominalisiert |
| **Possessives (DPOS)** | | | |
| `DPOSA` | POS | 60,599 | Attributiv |
| `DPOSN` | POS | 6,156 | Nominalisiert |
| `DPOSS` | POS | 705 | Substituierend |
| `DPOSD` | POS | 60 | Adverbial — stays POS (confirmed Katharina) |
| **Relative (DREL)** | | | |
| `DRELS` | PRO | 26,784 | Substituierend (confirmed) |
| **Interrogative (DW)** | | | |
| `DWA` | DET | 481 | Attributiv (welch-) |
| `DWS` | PRO | 151 | Substituierend |
| `DWD` | ADV | 20 | Adverbial |
| **Generalized (DG = swelch-)** | | | |
| `DGA` | DET | 507 | Attributiv (confirmed Katharina) |
| `DGS` | PRO | 173 | Substituierend (confirmed Katharina) |
| **Pronouns** | | | |
| `PPER` | PRO | 211,312 | Personal |
| `PRF` | PRO | 10,892 | Reflexive |
| `PI` | PRO | 7,366 | Indefinite |
| `PW` | PRO | 3,997 | Interrog./relative (default PRO; could be IPA) |
| `PG` | PRO | 3,979 | Possessive standalone |
| **Prepositions** | | | |
| `APPR` | PRP | 163,421 | Preposition |
| **Pronominal Adverbs (PAV)** | | | |
| `PAVAP` | ADV | 16,809 | Prepositional (dâvon, dâmite) |
| `PAVD` | ADV | 16,262 | Demonstrative (dâr+Präp) |
| `PAVW` | ADV | 472 | Interrogative (wâr+Präp) — ADV not IPA: lexical adverbs |
| `PAVG` | ADV | 23 | Generalized (swâr+Präp) |
| **Particles** | | | |
| `PTKNEG` | NEG | 25,111 | Negation (niht, ne, en) |
| `PTKVZ` | ADV | 13,992 | Separated verbal particle |
| `PTKA` | ADV | 989 | Adverbial particle |
| `PTKANT` | INJ | 349 | Answer particle (jâ, nein) — confirmed Katharina |
| **Verbs: Full (VV)** | | | |
| `VVFIN` | VRB | 159,470 | Finite |
| `VVINF` | VRB | 47,228 | Infinitive |
| `VVPP` | VRB | 43,503 | Past participle |
| `VVIMP` | VRB | 12,602 | Imperative |
| `VVPS` | VRB | 1,687 | Present participle |
| `VV` | VRB | 2 | Annotation artifact |
| **Verbs: Auxiliary (VA) — overcounts VEX** | | | |
| `VAFIN` | VEX | 87,282 | Finite |
| `VAINF` | VEX | 7,283 | Infinitive |
| `VAPP` | VEX | 1,019 | Past participle |
| `VAIMP` | VEX | 536 | Imperative |
| `VAPS` | VEX | 35 | Present participle |
| **Verbs: Modal (VM)** | | | |
| `VMFIN` | VEM | 43,359 | Finite |
| `VMINF` | VEM | 73 | Infinitive |
| `VMIMP` | VEM | 52 | Imperative |
| `VMPP` | VEM | 3 | Past participle |
| `VMPS` | VEM | 2 | Present participle |
| **Conjunctions** | | | |
| `KON` | CCNJ | 93,916 | Coordinating |
| `KOUS` | SCNJ | 43,728 | Subordinating |
| `KOKOM` | ADV | 2,027 | Comparative particle (als, wie) |
| `KO*` | null | 22,473 | Ambiguous — excluded Phase 1 (confirmed Katharina) |
| **Cardinals** | | | |
| `CARDA` | NUM | 11,401 | Attributiv |
| `CARDS` | NUM | 3,062 | Substituierend |
| `CARDN` | NUM | 151 | Nominalisiert |
| `CARDD` | NUM | 114 | Adverbial |
| **Other** | | | |
| `ITJ` | INJ | 2,409 | Interjection |
| `AVD-KO*` | ADV | 503 | Comparative dem. adverb |
| **Excluded (null)** | | | |
| `$_` | null | 286,202 | Punctuation |
| `--` | null | 121,808 | Untagged |
| `FM` | null | 26,163 | Foreign material |

## Known Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| VA* → VEX overcount | Inflates VEX; copula uses (VRB) miscounted | Affects all models equally; document in paper |
| No IPA mapping | IPA undercount (AVW, PW default to ADV/PRO) | Phase 2 context-sensitive resolver |
| No DIG mapping | Roman numerals may be CARD* or FM | 0 support, documented |
| No CNJ mapping | General conjunction tag unused | KO* (excluded) could be source |
| KO* excluded | 22k tokens (0.9%) not evaluated | Phase 2 context-sensitive (Verbstellung) |

## Ambiguous Mappings (Phase 1 defaults)

| HiTS | Default | Could also be | Trigger |
|------|---------|--------------|---------|
| AVW | ADV | IPA | Direct question context |
| PW | PRO | IPA | Direct question context |
| ADJN | ADJ | NOM | Fully substantivized use |
| KO* | null | SCNJ/CCNJ/ADV | Context-dependent (excluded Phase 1) |
