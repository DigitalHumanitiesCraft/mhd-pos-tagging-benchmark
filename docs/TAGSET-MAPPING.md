# HiTS → MHDBDB Tagset Mapping — Rationale & Gap Analysis

Maps 73 HiTS POS tags (ReM v2.1) to 19 MHDBDB POS tags. The YAML file at `src/mhd_pos_benchmark/mapping/hits_to_mhdbdb.yaml` is the single source of truth for code.

**Related:** [HITS-TAGSET.md](HITS-TAGSET.md) (source tags with frequencies) · [MHDBDB-TAGSET.md](MHDBDB-TAGSET.md) (target tags with functional distinctions)

**Status:** VALIDATED — all 73 corpus tags mapped. 0 unmapped. Confirmed by Katharina 2026-03-16.
Corpus coverage: 2,122,630 mappable (82.3%) / 456,646 excluded (17.7%) of 2,579,276 total tokens.

## Mapping Principles

1. **Functional alignment:** MHDBDB distinguishes attribuierend (DET) vs. substituierend (PRO). HiTS suffixes `A`/`S`/`D`/`N` encode exactly this.
2. **Default for ambiguous:** Phase 1 uses a static default. Context-sensitive resolution deferred to Phase 2.
3. **`null` = excluded:** Punctuation, foreign material, untagged → not evaluated.
4. **Document known overcounts:** VA* → VEX overcounts because HiTS doesn't distinguish copula from auxiliary.

## Complete Mapping Table

### Confirmed Mappings (in YAML, validated against corpus)

| HiTS | → MHDBDB | Count | Rationale |
|------|----------|------:|-----------|
| `NA` | NOM | 387,767 | Common noun |
| `NE` | NAM | 52,593 | Proper noun |
| `ADJA` | ADJ | 61,846 | Attributive adjective |
| `ADJD` | ADJ | 29,626 | Predicative/adverbial adjective |
| `ADJS` | ADJ | 14,989 | Other adjective |
| `ADJN` | ADJ | 5,392 | Nominalized adj. Default ADJ; could be NOM if fully substantivized |
| `AVD` | ADV | 159,727 | Demonstrative adverb |
| `AVG` | ADV | 2,811 | General adverb |
| `AVW` | ADV | 5,211 | Interrogative adverb. Default ADV; could be IPA in direct questions |
| `DDART` | DET | 149,086 | Definite article |
| `DIART` | DET | 20,382 | Indefinite article |
| `PPER` | PRO | 211,312 | Personal pronoun |
| `PRF` | PRO | 10,892 | Reflexive pronoun |
| `PI` | PRO | 7,366 | Indefinite pronoun |
| `PW` | PRO | 3,997 | Interrog./relative pronoun. Default PRO; could be IPA |
| `PG` | PRO | 3,979 | Possessive pronoun (standalone) |
| `APPR` | PRP | 163,421 | Preposition |
| `PTKNEG` | NEG | 25,111 | Negation particle |
| `PTKVZ` | ADV | 13,992 | Separated verbal particle |
| `PTKA` | ADV | 989 | Adverbial particle |
| `VVFIN` | VRB | 159,470 | Full verb, finite |
| `VVINF` | VRB | 47,228 | Full verb, infinitive |
| `VVPP` | VRB | 43,503 | Full verb, past participle |
| `VVIMP` | VRB | 12,602 | Full verb, imperative |
| `VVPS` | VRB | 1,687 | Full verb, present participle |
| `VAFIN` | VEX | 87,282 | Auxiliary, finite (overcounts — see Known Limitations) |
| `VAINF` | VEX | 7,283 | Auxiliary, infinitive |
| `VAPP` | VEX | 1,019 | Auxiliary, past participle |
| `VAIMP` | VEX | 536 | Auxiliary, imperative |
| `VAPS` | VEX | 35 | Auxiliary, present participle |
| `VMFIN` | VEM | 43,359 | Modal, finite |
| `VMINF` | VEM | 73 | Modal, infinitive |
| `VMIMP` | VEM | 52 | Modal, imperative |
| `VMPP` | VEM | 3 | Modal, past participle |
| `VMPS` | VEM | 2 | Modal, present participle |
| `KON` | CCNJ | 93,916 | Coordinating conjunction |
| `KOUS` | SCNJ | 43,728 | Subordinating conjunction |
| `KOKOM` | ADV | 2,027 | Comparative particle (als, wie) → ADV per MHDBDB rules |
| `ITJ` | INJ | 2,409 | Interjection |
| `FM` | null | 26,163 | Foreign material → excluded |
| `--` | null | 121,808 | Untagged → excluded |

### Proposed Mappings (unmapped, need confirmation)

Confirmed by Katharina (2026-03-16). Now in YAML.

| HiTS | → MHDBDB | Count | Rationale | Confidence |
|------|----------|------:|-----------|------------|
| **Punctuation** | | | | |
| `$_` | null | 286,202 | Punctuation → excluded | High |
| **Demonstrative Det/Pro (DD)** | | | | |
| `DDA` | DET | 13,383 | Attributiv → DET | High |
| `DDS` | PRO | 46,155 | Substituierend → PRO | High |
| `DDD` | ADV | 1,036 | Adverbial → ADV | Medium |
| `DDN` | PRO | 287 | Nominalisiert → PRO (substantiviert) | Medium |
| **Indefinite Det/Pro (DI)** | | | | |
| `DIA` | DET | 29,766 | Attributiv → DET | High |
| `DIS` | PRO | 7,181 | Substituierend → PRO | High |
| `DID` | ADV | 2,034 | Adverbial → ADV | Medium |
| `DIN` | PRO | 1,299 | Nominalisiert → PRO | Medium |
| **Possessive (DPOS)** | | | | |
| `DPOSA` | POS | 60,599 | Possessiv attributiv → POS | High |
| `DPOSS` | POS | 705 | Possessiv substituierend → POS | High |
| `DPOSN` | POS | 6,156 | Possessiv nominalisiert → POS | Medium |
| `DPOSD` | POS | 60 | Possessiv adverbial → stays POS. **Confirmed by Katharina.** | High |
| **Relative (DREL)** | | | | |
| `DRELS` | PRO | 26,784 | Relative = substituierend → PRO. **Confirmed.** | High |
| **Interrogative Det (DW)** | | | | |
| `DWA` | DET | 481 | Attributiv → DET (welch-) | High |
| `DWS` | PRO | 151 | Substituierend → PRO | High |
| `DWD` | ADV | 20 | Adverbial → ADV | Medium |
| **Other D (DG)** | | | | |
| `DGA` | DET | 507 | Generalized (swelch-), attributiv → DET. **Confirmed by Katharina.** | High |
| `DGS` | PRO | 173 | Generalized (swelch-), substituierend → PRO. **Confirmed by Katharina.** | High |
| **Cardinals (CARD)** | | | | |
| `CARDA` | NUM | 11,401 | Cardinal attributiv | High |
| `CARDS` | NUM | 3,062 | Cardinal substituierend | High |
| `CARDN` | NUM | 151 | Cardinal nominalisiert | High |
| `CARDD` | NUM | 114 | Cardinal adverbial | High |
| **Pronominal Adverbs (PAV)** | | | | |
| `PAVAP` | ADV | 16,809 | Prepositional pronominal adverb. **Confirmed.** | High |
| `PAVD` | ADV | 16,262 | Demonstrative pronominal adverb. **Confirmed.** | High |
| `PAVW` | ADV | 472 | Interrogative pronominal adverb → ADV (not IPA). **Confirmed by Christian:** warumbe/warzuo are lexical interrogative adverbs, not question-introducing particles. IPA is reserved for particles. | High |
| `PAVG` | ADV | 23 | General pronominal adverb | High |
| **Conjunctions** | | | | |
| `KO*` | null | 22,473 | Ambiguous conjunction (SCNJ/CCNJ/ADV). Excluded Phase 1, context-sensitive Phase 2. **Confirmed by Katharina.** | High |
| `AVD-KO*` | ADV | 503 | Comparative dem. adverb | Medium |
| **Particles** | | | | |
| `PTKANT` | INJ | 349 | Answer particle (jâ, nein) → INJ. **Confirmed by Katharina.** | High |
| **Bare base tags** | | | | |
| `ADJ` | ADJ | 2 | Annotation artifact | High |
| `VV` | VRB | 2 | Annotation artifact | High |

## Open Questions for Katharina

### Q1: Suffix Semantics
Ist das Suffix-System korrekt: `A`=attributiv, `S`=substituierend, `D`=adverbial, `N`=nominalisiert? Gibt es eine ReM-Dokumentation dazu?

### Q2: DG vs. DPOS
Was ist der Unterschied zwischen `DG*` (DGA, DGS — 680 Tokens) und `DPOS*` (67k Tokens)? Beides Possessiva? Oder hat DG eine andere Bedeutung?

### Q3: DRELS
Nur substituierend vorhanden (26k). Ist es korrekt, alle als PRO zu mappen? Oder gibt es Fälle, wo Relativpronomen als DET gelten?

### Q4: KO* (Asterisk-Tags)
22k Tokens mit `KO*`. Bedeutung: ambig zwischen koordinierend/subordinierend? Sollen wir diese ausschließen (null) oder mit Default mappen? Gibt es eine ReM-Konvention?

### Q5: PTKANT
349 Answer-Partikel. MHDBDB hat keine eigene Kategorie. Am nächsten: INJ (Interjektion) oder ADV?

### Q6: PAVW
472 interrogative Pronominaladverbien. Default ADV oder IPA (da interrogativ)?

### Q7: DPOSD / D-Suffix generell
Adverbial gebrauchte Possessiva/Determinanten — ADV oder bei der Ursprungskategorie lassen?

## Known Limitations

### VA* → VEX Overcount
HiTS tags all auxiliaries as VA*. MHDBDB distinguishes VRB (copula: *ist guot*) from VEX (with Partizip II: *hât gesehen*). Our mapping sends all VA* → VEX, which overcounts VEX. A context-sensitive resolver would need syntactic analysis (Phase 2+).

### No IPA Mapping
MHDBDB's IPA (Interrogativpartikel) has no direct HiTS equivalent. Candidates are AVW, PW, PAVW in interrogative contexts. Phase 1 maps all to ADV/PRO by default. Systematic undercount of IPA expected.

### No DIG Mapping
MHDBDB's DIG (Roman numerals) has no HiTS equivalent. Roman numerals in ReM may be tagged as CARD* or FM. DIG will show 0 support in evaluation.

### No CNJ Mapping
MHDBDB's general CNJ tag has no direct HiTS source. KO* could be a candidate if it means "ambiguous conjunction."

## Tags in YAML to Remove (not in corpus)

These were in the draft YAML based on HiTS docs but do not occur in ReM v2.1:

```
DD, DDSUB, DI, DISUB, DG, DGPOS, DGSUB, DP, DW, DWSUB,
PISUB, PGSUB, PWSUB, PDSUB, PPRO, PD,
APPO, APZR, APPRART,
PTKN, PTKV,
AVNEG, AVD-KO,
CARD,
KOUI,
$,, $., $(, $;, $:, XY
```

Removing these won't affect functionality (they'd never match), but cleaning the YAML improves clarity.
