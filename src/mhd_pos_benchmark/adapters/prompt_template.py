"""Prompt template for LLM-based POS tagging of Middle High German.

Derived from the MHDBDB pos-disambiguator skill but adapted for fresh tagging
(assigning tags from scratch, not disambiguating existing compound tags).

The template is shared across all LLM adapters (Gemini, Claude, etc.).
"""

# System prompt: establishes the LLM as a MHG linguistics expert
SYSTEM_PROMPT = """\
You are a specialist in Middle High German (MHG) linguistics. Your task is to \
assign a Part-of-Speech tag to each word in a MHG text.

## Valid Tags (closed set — use ONLY these)

| Tag  | Category                  | Examples                              |
|------|---------------------------|---------------------------------------|
| NOM  | Noun                      | acker, zît, minne                     |
| NAM  | Proper noun               | Uolrîch, Wiene, sant (before names)  |
| ADJ  | Adjective                 | grôz, schoene, guot                   |
| ADV  | Adverb                    | schone, vil, sêre, als (comparative)  |
| DET  | Determiner                | der, diu, daz, ein, diser, jener      |
| POS  | Possessive                | mîn, dîn, unser                       |
| PRO  | Pronoun                   | ich, ez, wir, relative pronouns       |
| PRP  | Preposition               | ûf, zuo, under, durch                 |
| NEG  | Negation                  | niht, nit, ne, en, âne                |
| NUM  | Numeral                   | zwô, drî                              |
| SCNJ | Subordinating conjunction | daz (clause), ob, swenne              |
| CCNJ | Coordinating conjunction  | und, oder, aber, ouch                 |
| VRB  | Full verb                 | liuhten, varn, machen                 |
| VEX  | Auxiliary verb            | haben/sîn/werden + Partizip II        |
| VEM  | Modal verb                | müezen, suln, kunnen                  |
| INJ  | Interjection              | ahî, owê, jâ, nein                   |

## Critical Distinctions

- **DET vs PRO**: DET modifies a noun (der man), PRO replaces a noun (der = he).
- **DET vs SCNJ**: daz + noun → DET; daz introducing verb-final clause → SCNJ.
- **VRB vs VEX**: VEX only with Partizip II (hât gesehen). Copula sîn + ADJ/NOM → VRB.
- **NEG**: niht, nit, nich, ne, en are ALWAYS NEG, never PRO.
- **NAM**: sant before proper names → NAM, not ADJ.
- **ADV**: comparative als/wie → ADV, not conjunction. vür wâr → ADV.
- **POS**: mîn, dîn, sîn, unser → POS (separate class, not DET).

## Output Format

Return ONLY a JSON array of tags, one per word, in the same order as the input. \
No explanations, no markdown, no extra text. Example:

Input: sô sprach der rîter
Output: ["ADV", "VRB", "DET", "NOM"]
"""


def build_tagging_prompt(forms: list[str], context_window: int = 0) -> str:
    """Build the user prompt with the token list.

    Args:
        forms: List of diplomatic word forms to tag.
        context_window: Not used yet — reserved for future windowed processing.

    Returns:
        The user message string.
    """
    # Number each word so the LLM can track position
    numbered = "\n".join(f"{i+1}. {form}" for i, form in enumerate(forms))
    return f"Tag each word with exactly one POS tag.\n\n{numbered}"


def build_chunked_prompts(
    forms: list[str],
    chunk_size: int = 200,
    overlap: int = 0,
) -> list[tuple[int, int, str]]:
    """Split a long token list into chunks for LLM processing.

    Returns list of (start_idx, end_idx, prompt_text) tuples.
    Overlap is reserved for future context-window experiments.
    """
    chunks = []
    for start in range(0, len(forms), chunk_size):
        end = min(start + chunk_size, len(forms))
        chunk_forms = forms[start:end]
        prompt = build_tagging_prompt(chunk_forms)
        chunks.append((start, end, prompt))
    return chunks
