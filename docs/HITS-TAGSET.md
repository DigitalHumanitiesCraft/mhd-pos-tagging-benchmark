# HiTS Tagset — As Actually Used in ReM v2.1

Reference for the HiTS POS tags as they appear in the ReM CORA-XML corpus (2,579,276 tokens, 406 documents). Based on Dipper et al. 2013, but the suffix system (A/S/D/N) is more extensive in practice than the publication documents.

**Source:** Empirical scan of `ReM-v2.1_coraxml/`, 2026-03-16.
**Base reference:** Dipper, Stefanie; Donhauser, Karin; Klein, Thomas; Linde, Sonja; Müller, Stefan; Wegera, Klaus-Peter (2013). "HiTS: ein Tagset für historische Sprachstufen des Deutschen." JLCL 28(1), S. 85–137.
**Note:** HiTS defines 12 word classes with 84 POS tags. ReM v2.1 uses 73 of these.
**Related:** [TAGSET-MAPPING.md](TAGSET-MAPPING.md) (HiTS → MHDBDB mapping) · [MHDBDB-TAGSET.md](MHDBDB-TAGSET.md) (target tagset)

## Suffix System

HiTS tags in ReM use functional suffixes on determiner, pronoun, cardinal, and pronominal adverb categories:

| Suffix | Function | Linguistic term |
|--------|----------|-----------------|
| `A` | attributiv — modifies a noun | attribuierend |
| `S` | substituierend — replaces a noun | substituierend (pronominal) |
| `D` | adverbial — used as adverb | adverbial |
| `N` | nominalisiert — used as noun | substantiviert |
| `ART` | article use | bestimmter/unbestimmter Artikel |

Example: `DD` (demonstrative determiner) → `DDA` (attr.), `DDS` (subst.), `DDD` (adv.), `DDN` (nom.), `DDART` (article)

## Complete Tag Inventory (73 tags)

### Nouns (440,360 tokens — 17.1%)

| Tag | Count | Description |
|-----|------:|-------------|
| `NA` | 387,767 | Common noun (Appellativum) |
| `NE` | 52,593 | Proper noun (Eigenname) |

### Adjectives (111,856 — 4.3%)

| Tag | Count | Description |
|-----|------:|-------------|
| `ADJA` | 61,846 | Attributive adjective |
| `ADJD` | 29,626 | Predicative/adverbial adjective |
| `ADJS` | 14,989 | Other adjective |
| `ADJN` | 5,392 | Nominalized adjective |
| `ADJ` | 2 | Bare base tag (likely annotation error) |

### Adverbs (168,252 — 6.5%)

| Tag | Count | Description |
|-----|------:|-------------|
| `AVD` | 159,727 | Demonstrative adverb (dâ, hie, sô) |
| `AVW` | 5,211 | Interrogative/relative adverb (wâ, wie) |
| `AVG` | 2,811 | General adverb |

### Determiners — `D*` (360,275 — 14.0%)

| Tag | Count | Description |
|-----|------:|-------------|
| **Demonstrative (DD)** | | |
| `DDART` | 149,086 | Demonstrative as article (der, diu, daz) |
| `DDS` | 46,155 | Demonstrative, substituierend |
| `DDA` | 13,383 | Demonstrative, attributiv |
| `DDD` | 1,036 | Demonstrative, adverbial |
| `DDN` | 287 | Demonstrative, nominalisiert |
| **Indefinite (DI)** | | |
| `DIA` | 29,766 | Indefinite, attributiv |
| `DIART` | 20,382 | Indefinite article (ein) |
| `DIS` | 7,181 | Indefinite, substituierend |
| `DID` | 2,034 | Indefinite, adverbial |
| `DIN` | 1,299 | Indefinite, nominalisiert |
| **Possessive (DPOS)** | | |
| `DPOSA` | 60,599 | Possessive, attributiv |
| `DPOSN` | 6,156 | Possessive, nominalisiert |
| `DPOSS` | 705 | Possessive, substituierend |
| `DPOSD` | 60 | Possessive, adverbial |
| **Relative (DREL)** | | |
| `DRELS` | 26,784 | Relative, substituierend |
| **Interrogative (DW)** | | |
| `DWA` | 481 | Interrogative, attributiv (welch-) |
| `DWS` | 151 | Interrogative, substituierend |
| `DWD` | 20 | Interrogative, adverbial |
| **Genitive/other (DG)** | | |
| `DGA` | 507 | DG attributiv |
| `DGS` | 173 | DG substituierend |

### Pronouns (237,546 — 9.2%)

| Tag | Count | Description |
|-----|------:|-------------|
| `PPER` | 211,312 | Personal pronoun (ich, du, er) |
| `PRF` | 10,892 | Reflexive pronoun (sich) |
| `PI` | 7,366 | Indefinite pronoun |
| `PW` | 3,997 | Interrogative/relative pronoun (wer, waz) |
| `PG` | 3,979 | Possessive pronoun (standalone) |

### Prepositions (163,421 — 6.3%)

| Tag | Count | Description |
|-----|------:|-------------|
| `APPR` | 163,421 | Preposition |

Note: `APPO`, `APZR`, `APPRART` from HiTS docs — **not found** in ReM v2.1.

### Pronominal Adverbs — `PAV*` (33,566 — 1.3%)

| Tag | Count | Description |
|-----|------:|-------------|
| `PAVAP` | 16,809 | Prepositional pronominal adverb (dâvon, dâmite) |
| `PAVD` | 16,262 | Demonstrative pronominal adverb |
| `PAVW` | 472 | Interrogative pronominal adverb (wâvon) |
| `PAVG` | 23 | General pronominal adverb |

### Particles (40,441 — 1.6%)

| Tag | Count | Description |
|-----|------:|-------------|
| `PTKNEG` | 25,111 | Negation particle (niht, ne, en) |
| `PTKVZ` | 13,992 | Separated verbal particle |
| `PTKA` | 989 | Adverbial particle |
| `PTKANT` | 349 | Answer particle (jâ, nein) |

Note: `PTKN` from HiTS docs — **not found** in ReM v2.1 (corpus uses `PTKNEG`).

### Verbs (403,334 — 15.6%)

| Tag | Count | Description |
|-----|------:|-------------|
| **Full (VV)** | | |
| `VVFIN` | 159,470 | Finite |
| `VVINF` | 47,228 | Infinitive |
| `VVPP` | 43,503 | Past participle |
| `VVIMP` | 12,602 | Imperative |
| `VVPS` | 1,687 | Present participle |
| `VV` | 2 | Bare tag (annotation error?) |
| **Auxiliary (VA)** | | |
| `VAFIN` | 87,282 | Finite |
| `VAINF` | 7,283 | Infinitive |
| `VAPP` | 1,019 | Past participle |
| `VAIMP` | 536 | Imperative |
| `VAPS` | 35 | Present participle |
| **Modal (VM)** | | |
| `VMFIN` | 43,359 | Finite |
| `VMINF` | 73 | Infinitive |
| `VMIMP` | 52 | Imperative |
| `VMPP` | 3 | Past participle |
| `VMPS` | 2 | Present participle |

### Conjunctions (162,144 — 6.3%)

| Tag | Count | Description |
|-----|------:|-------------|
| `KON` | 93,916 | Coordinating (und, oder, aber) |
| `KOUS` | 43,728 | Subordinating with finite verb (daz, ob) |
| `KO*` | 22,473 | **Ambiguous** conjunction (asterisk = unresolved) |
| `KOKOM` | 2,027 | Comparative particle (als, wie) |

Note: `KOUI` from HiTS docs — **not found** in ReM v2.1.

### Cardinals (14,728 — 0.6%)

| Tag | Count | Description |
|-----|------:|-------------|
| `CARDA` | 11,401 | Cardinal, attributiv |
| `CARDS` | 3,062 | Cardinal, substituierend |
| `CARDN` | 151 | Cardinal, nominalisiert |
| `CARDD` | 114 | Cardinal, adverbial |

Note: Bare `CARD` from HiTS docs — **not found** in ReM v2.1. Suffix system applies.

### Other

| Tag | Count | Description |
|-----|------:|-------------|
| `$_` | 286,202 | Punctuation (generic variant) |
| `--` | 121,808 | Untagged / missing annotation |
| `FM` | 26,163 | Foreign material (Latin, etc.) |
| `ITJ` | 2,409 | Interjection |
| `AVD-KO*` | 503 | Comparative demonstrative adverb (ambig.) |

## Tags in YAML Draft but NOT in Corpus

These tags from the HiTS documentation do not appear in ReM v2.1:

`DD`, `DDSUB`, `DI`, `DISUB`, `DG`, `DGPOS`, `DGSUB`, `DP`, `DW`, `DWSUB`,
`PISUB`, `PGSUB`, `PWSUB`, `PDSUB`, `PPRO`, `PD`,
`APPO`, `APZR`, `APPRART`,
`PTKN`, `PTKV`,
`AVNEG`, `AVD-KO`,
`CARD`,
`KOUI`,
`$,`, `$.`, `$(`, `$;`, `$:`, `XY`

## Tags in Corpus but NOT in YAML Draft

See [TAGSET-MAPPING.md](TAGSET-MAPPING.md) for the full gap analysis with proposed mappings.
