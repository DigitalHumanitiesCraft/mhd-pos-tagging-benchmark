# MHDBDB POS Tagset (19 Tags)

The MHDBDB (Mittelhochdeutsche Begriffsdatenbank) uses a 19-tag Part-of-Speech tagset for Middle High German. This document is the authoritative reference for the benchmark's target tagset.

**Source:** Exported from `mhdbdb-tei-only/.gemini/skills/pos-disambiguator/SKILL.md`

## Tag Table

**CRITICAL: "ART" is NOT a valid tag.** Articles are tagged as **DET**.

| Tag | Name | Examples |
|-----|------|----------|
| **NOM** | Nomen (Noun) | acker, zît, minne |
| **NAM** | Name (Proper noun) | Uolrîch, Wiene, Rhîn, sant (before names) |
| **ADJ** | Adjektiv (Adjective) | grôz, schoene, guot, wâr |
| **ADV** | Adverb | schone, vil, sêre, gar, als (comparative), wie (comparative) |
| **DET** | Determinante (Determiner) | der, diu, daz, ein, eine, diser, jener, kein, dekein, dehein |
| **POS** | Possessivpronomen | mîn, dîn, unser |
| **PRO** | Pronomen (Pronoun) | ich, ez, wir, relative pronouns, swer (indefinite) |
| **PRP** | Präposition (Preposition) | ûf, zuo, under, durch |
| **NEG** | Negation | nie, niht, nit, nich, nieht, niet, niut, nyt, ne, en, âne |
| **NUM** | Numeral | zwô, drî, zweinzegest |
| **CNJ** | Konjunktion (general) | danne (when ambiguous) |
| **SCNJ** | Subordinierende Konj. | daz (clause), ob, swenne, sît, als (temporal), wie (subordinating) |
| **CCNJ** | Koordinierende Konj. | und, oder, aber, ouch, noch |
| **IPA** | Interrogativpartikel | wie (interrogative), war (wohin?), swer (interrogative) |
| **VRB** | Verb (Full verb) | liuhten, varn, machen, haben/sîn/werden (lexical) |
| **VEX** | Hilfsverb (Auxiliary) | haben/sîn/werden (with Partizip II) |
| **VEM** | Modalverb (Modal verb) | müezen, suln, kunnen |
| **INJ** | Interjektion | ahî, owê |
| **DIG** | Zahl (Roman numeral) | IX, XVII, III |

## Functional Distinctions

### DET vs PRO (attribuierend vs. substituierend)

| Function | Tag | Examples |
|----------|-----|----------|
| **Attribuierend** (modifies noun) | DET | der man, diu frouwe, ein hûs, diser tac |
| **Substituierend** (replaces noun) | PRO | der (= he/that one), daz (= that), swer (whoever) |

- Articles (der, diu, daz, ein) → **DET** when modifying a noun
- Same forms standing alone (replacing noun) → **PRO**
- Relative pronouns → **PRO** (always substituierend)

### POS as Separate Class

Possessives (mîn, dîn, unser) are a **separate class (POS)**, not DET, due to morphological distinctiveness — they encode person and number of the possessor.

### DET vs PRO vs SCNJ (*daz*, *der*)

- *daz* + noun phrase → **DET**
- *daz* introducing verb-final clause → **SCNJ** (*ich weiz daz er kumt*)
- *daz* standing alone (= "that") → **PRO**
- *daz* pointing deictically to prior content → **DET** (NOT PRO!) (*daz ist wâr* = "dies ist wahr")
- *der* + noun → **DET**
- *der* as relative pronoun → **PRO**

### VRB vs VEX (Full verb vs. Auxiliary)

| Pattern | Tag |
|---------|-----|
| With Partizip II → Perfect/Passive | **VEX** (*hât gesehen*, *ist komen*, *wirt geslagen*) |
| Copula + NP/ADJ (no Partizip) | **VRB** (*ist guot*, *ist ein rîter*) |
| Possession/lexical meaning | **VRB** (*hân ein hûs*) |

### als, wie: Context-Dependent

| Context | Tag |
|---------|-----|
| Temporal/causal subordination | SCNJ (*als er kam*) |
| **Comparative particle** | **ADV** (*grœzer als ein man*) |
| **Direct question** | **IPA** (*wie tuost du daz?*) |
| Subordinating (indirect) | SCNJ (*ich weiz wie er daz tet*) |

**Important:** Comparative *als* and *wie* are NOT conjunctions → **ADV**.

### war: 5-Way Ambiguity

| Meaning | Tag |
|---------|-----|
| "wohin" (interrogative) | IPA |
| "wahr" (true) | ADJ |
| "woher/wo" (locative) | ADV |
| Form of sîn/wesen (full verb) | VRB |
| Form of sîn/wesen (auxiliary) | VEX |

### Compound Tags (Morphological Fusions Only)

Most words get ONE tag. Two tags only for genuine morphological fusions:
- Verb + enclitic pronoun: *wiltu* = wilt + du → `VEM PRO`
- Preposition + determiner: *zer* = ze + der → `PRP DET`

## Known Error Patterns (from LLM Disambiguation)

These are documented recurring errors when LLMs tag MHG texts:

| Error | Wrong | Correct | Rule |
|-------|-------|---------|------|
| niht, nit, nich, ne, en tagged as pronoun | PRO | **NEG** | MHG negation forms are NEVER pronominal |
| *sant* before proper names tagged as adjective | ADJ | **NAM** | Fixed onymic title ("Sankt"), not attributive adjective |
| Deictic *daz* (pointing to prior content) tagged as pronoun | PRO | **DET** | If not introducing subordinate clause → DET |
| *kein/dekein/dehein* before noun tagged as pronoun | PRO | **DET** | Indefinite determiners when modifying noun |
| *wâr* in *vür wâr* tagged as noun | NOM | **ADV** | Fixed adverbial phrase meaning "truly" |
| MHG reinforced negation misunderstood | — | — | Multiple NEG particles reinforce (not cancel) negation |

## MHG Negation (Critical for Evaluation)

MHG uses **reinforced negation** — multiple NEG particles in one clause strengthen the negation:
- *ne vil ensanc er niht* = "he didn't sing at all" (NOT double-negative cancellation)
- Each negation particle (ne, niht, nit, etc.) is tagged NEG individually
- ALL forms: niht, nichtes, nit, nich, nieht, niet, niut, nyt, ne, en, n → **NEG** (NEVER PRO)
