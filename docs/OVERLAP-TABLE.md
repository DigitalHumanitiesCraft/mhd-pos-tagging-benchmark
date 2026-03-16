# ReM ↔ MHDBDB Text Overlap

Mapping of overlapping texts between ReM (Referenzkorpus Mittelhochdeutsch) and MHDBDB (Mittelhochdeutsche Begriffsdatenbank). Compiled by Katharina (March 2026).

**Status:** Edition matching deferred — needs manual philological review to confirm identical text bases. Michael to assign HiWi for this task.

**Genre bias:** Overlap is heavily epic-focused. Lyric texts barely overlap. Non-epic examples: "Das Buch von guter Speise" (cookbook), "Engelthaler Schwesternbuch" (religious prose).

## Overlap Table

| rem_id | rem_title | mhdbdb_id | mhdbdb_title |
|--------|-----------|-----------|--------------|
| M008 | Straßburger Alexander | AXS | Lambrechts Alexander (Strassburger Hs.) |
| M009 | Pfaffe Lambrecht: Alexanderlied (Vorauer Alexander) | AXV | Lamprechts Alexander (Vorauer Hs.) |
| M013B | Annolied (V: Bonaventura Vulcanius) | ANN | Annolied |
| M013O | Annolied (O: Opitz) | ANN | Annolied |
| M064M | Eilhart von Oberg: Tristrant (M) | EID | Tristrant |
| M064R | Eilhart von Oberg: Tristrant (R) | EID | Tristrant |
| M064S | Eilhart von Oberg: Tristrant (St) | EID | Tristrant |
| M100 | Graf Rudolf | RUD | Graf Rudolf |
| M106 | Heinrich: Reinhart Fuchs (S) | RF | Reinhart Fuchs |
| M108M | Herzog Ernst A (M) | ERA | Herzog Ernst A |
| M108P | Herzog Ernst A (P) | ERA | Herzog Ernst A |
| M108S | Herzog Ernst A (S) | ERA | Herzog Ernst A |
| M109 | Himmel und Hölle | HH | Himmel und Hölle |
| M119 | Die Jüngere Judith | JUD | Die jüngere Judith |
| M121F | Kaiserchronik A (F: Fragmente Fr, Mz) | KC1 | Kaiserchronik |
| M121G | Kaiserchronik A (G: Fragmente Gr, I) | KC1 | Kaiserchronik |
| M121K | Kaiserchronik A (Fragment K) | KC1 | Kaiserchronik |
| M121N | Kaiserchronik A (Fragment N) | KC1 | Kaiserchronik |
| M121S | Kaiserchronik A (Fragment S) | KC1 | Kaiserchronik |
| M121V | Kaiserchronik A (V) [Ausschnitt] | KC1 | Kaiserchronik |
| M121W | Kaiserchronik A (Fragment W) | KC1 | Kaiserchronik |
| M121Y | Kaiserchronik A (V) | KC1 | Kaiserchronik |
| M206 | König Rother (H) | ROT | König Rother |
| M234 | Vaterunser | VAT | Vaterunser |
| M304 | Dietrichs Flucht (R) | DFL | Dietrichs Flucht |
| M321 | Nibelungenlied | NBB | Nibelungenlied B |
| M325 | Wolfram von Eschenbach: Parzival (D) | PZ | Parzival |
| M342 | Gottfried von Straßburg: Tristan | TR | Tristan |
| M343 | Ulrich von Türheim: Rennewart (B) | REN | Rennewart |
| M406 | Christine Ebner: Engelthaler Schwesternbuch (N2) | ESB | Engelthaler Schwesternbuch |
| M406Y | Christine Ebner: Engelthaler Schwesternbuch (N2) | ESB | Engelthaler Schwesternbuch |
| M503 | Albert von Augsburg: Leben des heiligen Ulrich | HUL | Leben des heiligen Ulrich |
| M510 | Gundacker von Judenburg: Christi Hort | CHH | Christi Hort |
| M522 | Sigenot | SIG | Sigenot |
| M529 | Gottfried Hagen: Reimchronik der Stadt Köln (D) | RCC | Reimchronik der Stadt Cöln |
| M539 | Das Buch von guter Speise (A) | DES2 | Das Buch von guter Speise |
| M539 | Das Buch von guter Speise (A) | GSP | Das Buch von guter Speise |
| M541B | Herbort von Fritzlar: Liet von Troye (B) | TRY | Liet von Troye |
| M541H | Herbort von Fritzlar: Liet von Troye (H) | TRY | Liet von Troye |
| M541S | Herbort von Fritzlar: Liet von Troye (S) | TRY | Liet von Troye |
| M548 | Prosa-Lancelot Msp | PL1, PL2, PL3 | Prosa-Lancelot |

## Notes

- **Multiple ReM versions per MHDBDB text:** KC1 (8 versions), EID (3), ERA (3), TRY (3), ANN (2), ESB (2). Useful for testing consistency across manuscript variants.
- **M539 maps to two MHDBDB sigles** (DES2 and GSP) — need to clarify which MHDBDB entry is canonical.
- **M548 maps to three MHDBDB volumes** (PL1, PL2, PL3) — Prosa-Lancelot is split in MHDBDB.
- **Edition field** in ReM `<header><edition>` and MHDBDB TEI headers must be compared to confirm text identity.
