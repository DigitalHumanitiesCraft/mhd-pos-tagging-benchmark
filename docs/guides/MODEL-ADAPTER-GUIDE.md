# How to Add Your Own Model

This guide shows how to plug any POS tagger into the benchmark — a fine-tuned BERT, a CRF, an HMM, a dictionary lookup, anything with Python bindings.

## The Contract

Implement one class with two things:

```python
from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.data.corpus import Document

class MyAdapter(ModelAdapter):
    @property
    def name(self) -> str:
        return "my-model-v1"

    def predict(self, document: Document) -> list[str]:
        # Return one MHDBDB tag per mappable token, in order
        ...
```

That's it. The benchmark handles everything else (parsing, mapping, metrics, reporting).

## What You Receive

`predict()` gets a `Document` with these useful fields:

```python
document.id                      # "M001" — unique document ID
document.mappable_tokens         # list[Token] — only the tokens you need to tag
document.tokens                  # list[Token] — all tokens (including excluded)

# Each Token has:
token.form_for_tagging           # "ritter" — the word form to tag
token.form_diplomatic            # "ritter" — original written form
token.form_modernized            # "ritter" — analyzed form (different for clitics)
token.lemma                      # "rîter" — lemma (may be None)
token.id                         # "t1_m1" — unique token ID
```

## What You Return

A `list[str]` of MHDBDB tags — exactly one per `document.mappable_tokens`, in the same order.

The 16 valid tags:

| Tag | Category | Tag | Category |
|-----|----------|-----|----------|
| NOM | Noun | PRP | Preposition |
| NAM | Proper noun | NEG | Negation |
| ADJ | Adjective | NUM | Numeral |
| ADV | Adverb | SCNJ | Subord. conjunction |
| DET | Determiner | CCNJ | Coord. conjunction |
| POS | Possessive | VRB | Full verb |
| PRO | Pronoun | VEX | Auxiliary verb |
| INJ | Interjection | VEM | Modal verb |

## Example: Dictionary Lookup

The simplest possible adapter — a hardcoded dictionary:

```python
# my_adapters/dictionary.py

from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.data.corpus import Document

# Minimal MHG word → tag dictionary
LEXICON = {
    "der": "DET", "diu": "DET", "daz": "DET", "ein": "DET",
    "ich": "PRO", "du": "PRO", "er": "PRO", "wir": "PRO",
    "und": "CCNJ", "oder": "CCNJ",
    "daz": "SCNJ",  # ambiguous! context would help
    "niht": "NEG", "ne": "NEG",
    "ist": "VEX", "was": "VEX", "hât": "VEX",
}

class DictionaryAdapter(ModelAdapter):
    @property
    def name(self) -> str:
        return "dictionary-lookup"

    def predict(self, document: Document) -> list[str]:
        return [
            LEXICON.get(token.form_for_tagging.lower(), "NOM")  # default: NOM
            for token in document.mappable_tokens
        ]
```

## Example: Hugging Face Transformer

A BERT-style token classifier fine-tuned on MHG POS:

```python
# my_adapters/bert_tagger.py

from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch

from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.data.corpus import Document

# Map your model's label IDs to MHDBDB tags
LABEL_MAP = {0: "NOM", 1: "VRB", 2: "ADJ", ...}  # from your training

class BertMhdAdapter(ModelAdapter):
    def __init__(self, model_path: str = "your-org/mhg-pos-bert"):
        self._tokenizer = AutoTokenizer.from_pretrained(model_path)
        self._model = AutoModelForTokenClassification.from_pretrained(model_path)
        self._model.eval()

    @property
    def name(self) -> str:
        return "bert-mhg-pos"

    def predict(self, document: Document) -> list[str]:
        forms = [t.form_for_tagging for t in document.mappable_tokens]
        # Tokenize — one word at a time to maintain alignment
        tags = []
        for form in forms:
            inputs = self._tokenizer(form, return_tensors="pt")
            with torch.no_grad():
                logits = self._model(**inputs).logits
            # Take the prediction for the first subword token
            label_id = logits[0, 1, :].argmax().item()  # skip [CLS]
            tags.append(LABEL_MAP.get(label_id, "NOM"))
        return tags
```

## Example: CRF Tagger

A classical CRF using hand-crafted features:

```python
# my_adapters/crf_tagger.py

import pickle
from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.data.corpus import Document

class CrfAdapter(ModelAdapter):
    def __init__(self, model_path: str = "models/mhg_crf.pkl"):
        with open(model_path, "rb") as f:
            self._model = pickle.load(f)

    @property
    def name(self) -> str:
        return "crf-mhg"

    def predict(self, document: Document) -> list[str]:
        # Extract features per token
        features = [
            {
                "word": t.form_for_tagging,
                "lemma": t.lemma or "",
                "suffix3": t.form_for_tagging[-3:],
                "is_upper": t.form_for_tagging[0].isupper(),
            }
            for t in document.mappable_tokens
        ]
        return self._model.predict([features])[0]
```

## Running Your Adapter

Custom adapters aren't registered in the CLI (yet). Use a small Python script:

```python
#!/usr/bin/env python3
"""Run the benchmark with a custom adapter."""

from pathlib import Path
from rich.console import Console

from mhd_pos_benchmark.data.rem_parser import parse_corpus
from mhd_pos_benchmark.mapping.tagset_mapper import TagsetMapper
from mhd_pos_benchmark.evaluation.comparator import align_corpus
from mhd_pos_benchmark.evaluation.metrics import compute_metrics
from mhd_pos_benchmark.evaluation.report import print_report, save_json

# 1. Import your adapter
from my_adapters.bert_tagger import BertMhdAdapter

# 2. Parse and map corpus
corpus_dir = Path("ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/")
documents = parse_corpus(corpus_dir)
mapper = TagsetMapper()
for doc in documents:
    mapper.map_document(doc)

# 3. Optional: use a subset for quick testing
from mhd_pos_benchmark.data.subset import select_subset
documents = select_subset(documents, n=10)

# 4. Run evaluation
adapter = BertMhdAdapter("your-org/mhg-pos-bert")
alignments = align_corpus(documents, adapter, continue_on_error=True)
result = compute_metrics(alignments, adapter.name)

# 5. Print and save
console = Console()
print_report(result, console)
save_json(result, Path(f"results/{adapter.name}.json"))
```

```bash
pip install -e "."
python run_my_model.py
```

## Checklist

Before running on the full corpus:

- [ ] `predict()` returns exactly `len(document.mappable_tokens)` tags
- [ ] All returned tags are in the 16-tag set (NOM, NAM, ADJ, ADV, DET, POS, PRO, PRP, NEG, NUM, SCNJ, CCNJ, VRB, VEX, VEM, INJ)
- [ ] Test on one small document first (`--subset 1` or `select_subset(docs, n=1)`)
- [ ] Check that `gold-passthrough` gives 100% before trusting your model's results

## Common Pitfalls

| Problem | Solution |
|---------|----------|
| Wrong number of tags returned | Only tag `document.mappable_tokens`, not `document.tokens`. Excluded tokens (punctuation, FM, untagged) don't get tags. |
| Tags not in the MHDBDB set | Map your model's output to the 16 MHDBDB tags. If your model uses a different tagset, add a translation step. |
| Clitics (`inder` = `in` + `der`) | Use `token.form_for_tagging` — it returns the analyzed form for clitics, not the combined written form. |
| Very slow on full corpus | The full ReM has 2.1M mappable tokens across 406 documents. Use `select_subset()` for development. |
