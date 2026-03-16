# CORA-XML Format Reference (ReM v2.1)

Reference for parsing ReM (Referenzkorpus Mittelhochdeutsch) CORA-XML files.

**Source:** https://www.linguistics.rub.de/rem/access/index.html
**Citation:** Roussel, Adam; Klein, Thomas; Dipper, Stefanie; Wegera, Klaus-Peter; Wich-Reif, Claudia (2024). Referenzkorpus Mittelhochdeutsch (1050–1350), Version 2.1. ISLRN 937-948-254-174-0.
**License:** CC BY-SA 4.0

## File Structure

```xml
<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE text SYSTEM "cora-xml.dtd">
<text id="M321">
  <header>
    <title>Nibelungenlied</title>
    <abbr_ddd>Nib</abbr_ddd>
    <abbr_mwb>NibC</abbr_mwb>
    <topic>Poesie</topic>
    <text-type>Heldenepik</text-type>
    <genre>V</genre>                        <!-- V=Vers, P=Prosa -->
    <edition>Ursula Hennig (Hg.), ...</edition>
    <language-area>westbairisch-ostalemannisch</language-area>
    <date>ca. 1180-1210</date>
    <text-author>-</text-author>
    <annotation_by>Wiebke Wolf (Bonn)</annotation_by>
    <!-- ... more metadata fields ... -->
  </header>
  <layoutinfo>...</layoutinfo>
  <shifttags>...</shifttags>

  <!-- Tokens and comments in document order -->
  <token id="t1" trans="auentiure" type="token">...</token>
  <comment type="K">/R</comment>
  <token id="t2" trans="von" type="token">...</token>
  ...
</text>
```

## Token Structure

### Simple Token (one word)

```xml
<token id="t1" trans="auentiure" type="token">
  <tok_dipl id="t1_d1" trans="auentiure" utf="auentiure"/>
  <tok_anno id="t1_m1" ascii="auentiure" trans="auentiure" utf="auentiure">
    <norm tag="âventiure"/>
    <lemma tag="âventiure"/>
    <lemma_gen tag="âventiure"/>
    <lemma_idmwb tag="10086000"/>
    <pos tag="NA"/>                   <!-- Instance-level POS (fine-grained) -->
    <pos_gen tag="NA"/>               <!-- Generalized POS (coarser) -->
    <infl tag="Nom.Sg"/>
    <inflClass tag="*.Fem"/>
    <inflClass_gen tag="*.Fem"/>
  </tok_anno>
</token>
```

### Multi-Mod Token (clitic/split)

When a written form contains multiple words (e.g., "inalten" = "in" + "alten"):

```xml
<token id="t10" trans="inalten" type="token">
  <tok_dipl id="t10_d1" trans="inalten" utf="inalten"/>
  <tok_anno id="t10_m1" ascii="in" trans="in|" utf="in">
    <norm tag="in"/>
    <token_type tag="MS1"/>           <!-- Morphological Split, part 1 -->
    <lemma tag="in"/>
    <pos tag="APPR"/>
    <pos_gen tag="AP"/>
  </tok_anno>
  <tok_anno id="t10_m2" ascii="alten" trans="|alten" utf="alten">
    <norm tag="alten"/>
    <token_type tag="MS2"/>           <!-- Morphological Split, part 2 -->
    <lemma tag="alt"/>
    <pos tag="ADJA"/>
    <pos_gen tag="ADJ"/>
  </tok_anno>
</token>
```

**Each `<tok_anno>` with a `<pos>` child = one benchmark token.**

## Key Elements

| Element | Description | Use for Benchmark |
|---------|-------------|-------------------|
| `<tok_dipl>` | Diplomatic transcription (as in manuscript) | Display only |
| `<tok_anno>` | Annotatable unit (modernized) | **Primary — POS tags live here** |
| `<pos tag="..."/>` | Instance-level POS (fine-grained, e.g., DDART, ADJA, VVFIN) | **Use this** |
| `<pos_gen tag="..."/>` | Generalized POS (coarser, e.g., DD, ADJ, VV) | Secondary reference |
| `<norm tag="..."/>` | Normalized form | Useful for alignment |
| `<lemma tag="..."/>` | Lemma | Useful for analysis |
| `<lemma_gen tag="..."/>` | Generalized lemma | Secondary |
| `<lemma_idmwb tag="..."/>` | MWB lemma ID | Cross-reference |
| `<infl tag="..."/>` | Inflection (case, number, etc.) | Future use |
| `<token_type tag="..."/>` | MS1/MS2 for morphological splits | Detect multi-mod tokens |

## Metadata Fields (in `<header>`)

| Field | Example | Use |
|-------|---------|-----|
| `<title>` | Nibelungenlied | Text identification |
| `<abbr_ddd>` | Nib | ReM sigle |
| `<genre>` | V (Vers), P (Prosa) | Genre stratification |
| `<text-type>` | Heldenepik | Subgenre |
| `<edition>` | Ursula Hennig (Hg.), ... | Edition matching with MHDBDB |
| `<language-area>` | westbairisch-ostalemannisch | Dialect analysis |
| `<date>` | ca. 1180-1210 | Dating |
| `<annotation_by>` | Wiebke Wolf (Bonn) | Annotator provenance |

## POS Tag Suffix System

HiTS tags use functional suffixes (A/S/D/N/ART) on determiners, cardinals, and pronominal adverbs. See [HITS-TAGSET.md](HITS-TAGSET.md) for the full inventory and [TAGSET-MAPPING.md](TAGSET-MAPPING.md) for how suffixes map to MHDBDB tags.

## Important Notes

1. **Element names differ from CORA-XML docs:** Actual files use `tok_anno` (not `mod`) and `tok_dipl` (not `dipl`)
2. **Two POS layers:** `<pos>` is instance-level (fine: DDART, APPR, ADJA), `<pos_gen>` is generalized (coarse: DD, AP, ADJ). **Use `<pos>` for evaluation.**
3. **`<comment>` elements** between tokens are structural markers (e.g., `/R` for line breaks). Skip them.
4. **Entity encoding:** `&lt;` `&gt;` in `trans` attributes (e.g., `Nib&lt;e&gt;lungen`). The `utf` attribute has the decoded form.
5. **406 parseable files** in ReM v2.1 CORA-XML corpus (407 in directory).
6. **`$_` is the dominant punctuation tag** (286k occurrences). The HiTS-documented variants `$.`, `$,`, `$(` etc. do not appear in ReM v2.1.
7. **`--` means untagged** (122k tokens). These have no POS annotation and are excluded from evaluation.
8. **`KO*` / `AVD-KO*`** — asterisk marks ambiguous annotation (22k + 500 tokens). Resolution strategy TBD.
