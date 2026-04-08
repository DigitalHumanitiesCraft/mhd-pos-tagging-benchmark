# How to Add Your Own Model

You have a POS tagger — a fine-tuned BERT, a CRF, an HMM, a dictionary, or anything else that can assign POS tags to Middle High German words. This guide shows you how to plug it into the benchmark so you can compare it against other models.

## Do I Need This Guide?

**No, if** you want to use an existing LLM (Claude, Gemini, GPT, Mistral, etc.). For those, use the built-in adapters — no code required:

```bash
# LLM via CLI tool (Claude, Gemini CLI, Codex, etc.)
mhd-bench evaluate --adapter cli --cli-cmd "claude -p --model opus" --model claude-opus-4.6

# LLM via API key (OpenAI, Gemini, Mistral, Groq, etc.)
mhd-bench evaluate --adapter api --provider gemini --model gemini-2.5-pro --api-key
```

See [GETTING-STARTED.md](GETTING-STARTED.md) for details.

**Yes, if** you have a custom model — something you trained, downloaded, or built yourself that runs as Python code. That's what this guide is for.

## What You Need

- Python 3.13+
- The benchmark installed (`pip install -e "."`)
- Your model accessible from Python (a local file, a Hugging Face model, a pickle, etc.)
- Basic familiarity with Python (writing a function, running a script)

## How It Works

The benchmark has a simple contract: you write a Python class with one method called `predict()`. The benchmark calls this method once per document, passes you the words, and you return the POS tags. That's it — the benchmark handles parsing the corpus, computing accuracy, and generating the report.

```
Your model                         The benchmark
────────────                       ─────────────
                    Document
              ◄──── (list of words)
                    
predict()
figures out
the POS tags
                    
              ────► list of tags     → accuracy, F1,
                    (one per word)     confusion matrix,
                                       comparison tables
```

## Step 1: Create Your Adapter File

Create a new Python file anywhere on your computer. For this example, we'll call it `my_tagger.py` and put it in the repo root:

```python
# my_tagger.py

from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.data.corpus import Document


class MyTagger(ModelAdapter):
    """Replace this with a description of your model."""

    @property
    def name(self) -> str:
        # A short name for your model — shows up in reports and filenames
        return "my-model-v1"

    def predict(self, document: Document) -> list[str]:
        # This is where your model does its work.
        # You receive a document and must return one POS tag per word.

        tags = []
        for token in document.mappable_tokens:
            word = token.form_for_tagging  # e.g., "ritter", "der", "sprach"

            # === YOUR MODEL LOGIC HERE ===
            # Replace this with however your model assigns tags.
            # For now, we just guess "NOM" for everything:
            tag = "NOM"

            tags.append(tag)

        return tags
```

**Key points:**
- `document.mappable_tokens` gives you only the words that need tagging (punctuation, foreign text, and untagged items are already excluded)
- `token.form_for_tagging` gives you the word form — use this, not `form_diplomatic` or `form_modernized` (it handles clitics correctly)
- You must return **exactly** `len(document.mappable_tokens)` tags — no more, no fewer

## Step 2: Use the Right Tags

Your model must return tags from this set of 16 — no other tags are accepted:

| Tag | What it means | Examples |
|-----|---------------|----------|
| NOM | Noun | ritter, minne, zît |
| NAM | Proper noun | Uolrîch, Wiene |
| ADJ | Adjective | grôz, schoene |
| ADV | Adverb | schone, vil, sêre |
| DET | Determiner | der, diu, ein |
| POS | Possessive | mîn, dîn, unser |
| PRO | Pronoun | ich, er, wir |
| PRP | Preposition | ûf, zuo, in |
| NEG | Negation | niht, ne, en |
| NUM | Numeral | zwô, drî |
| SCNJ | Subordinating conj. | daz (clause), ob |
| CCNJ | Coordinating conj. | und, oder, aber |
| VRB | Full verb | liuhten, varn |
| VEX | Auxiliary verb | hât (+ participle) |
| VEM | Modal verb | müezen, suln |
| INJ | Interjection | owê, jâ |

If your model uses a different tagset (e.g., STTS, Universal POS), you need a mapping step — translate your model's tags to these 16 before returning them.

## Step 3: Run the Benchmark

Create a runner script next to your adapter file. This script loads the corpus, runs your model, and shows the results:

```python
# run_my_tagger.py

from pathlib import Path
from rich.console import Console

from mhd_pos_benchmark.data.rem_parser import parse_corpus
from mhd_pos_benchmark.mapping.tagset_mapper import TagsetMapper
from mhd_pos_benchmark.data.subset import select_subset
from mhd_pos_benchmark.evaluation.comparator import align_corpus
from mhd_pos_benchmark.evaluation.metrics import compute_metrics
from mhd_pos_benchmark.evaluation.report import print_report, save_json

# Import YOUR adapter
from my_tagger import MyTagger

# --- Configuration (change these) ---
CORPUS_DIR = Path("ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/")
SUBSET_SIZE = 3   # Start small! Increase once it works.
# -------------------------------------

# Load and prepare corpus
print("Loading corpus...")
documents = parse_corpus(CORPUS_DIR)
mapper = TagsetMapper()
for doc in documents:
    mapper.map_document(doc)
documents = select_subset(documents, n=SUBSET_SIZE)
print(f"Testing on {len(documents)} documents")

# Run your model
adapter = MyTagger()
print(f"Running {adapter.name}...")
alignments = align_corpus(documents, adapter, continue_on_error=True)
result = compute_metrics(alignments, adapter.name)

# Show results
console = Console()
print_report(result, console)

# Save to JSON (optional)
save_json(result, Path(f"results/{adapter.name}.json"))
print(f"\nResults saved to results/{adapter.name}.json")
```

Run it:

```bash
python run_my_tagger.py
```

You should see a table with accuracy, per-tag precision/recall/F1, and token counts. Start with `SUBSET_SIZE = 3` (fast), then increase to `10` or remove the subset for the full corpus.

## Complete Examples

### Dictionary Lookup (simplest possible)

A hardcoded word-to-tag dictionary. Useful as a sanity check or minimal baseline:

```python
# dictionary_tagger.py

from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.data.corpus import Document

LEXICON = {
    "der": "DET", "diu": "DET", "daz": "DET", "ein": "DET",
    "ich": "PRO", "du": "PRO", "er": "PRO", "wir": "PRO",
    "und": "CCNJ", "oder": "CCNJ",
    "niht": "NEG", "ne": "NEG",
    "ist": "VEX", "was": "VEX", "hât": "VEX",
}

class DictionaryTagger(ModelAdapter):
    @property
    def name(self) -> str:
        return "dictionary-lookup"

    def predict(self, document: Document) -> list[str]:
        return [
            LEXICON.get(token.form_for_tagging.lower(), "NOM")  # guess NOM if unknown
            for token in document.mappable_tokens
        ]
```

### Hugging Face Transformer (BERT-style)

If you have a fine-tuned token classifier on Hugging Face:

```python
# bert_tagger.py

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.data.corpus import Document

# Map your model's numeric label IDs to MHDBDB tags.
# You defined these during training — check your label2id config.
LABEL_MAP = {0: "NOM", 1: "VRB", 2: "ADJ", 3: "ADV", 4: "DET", ...}

class BertMhdTagger(ModelAdapter):
    def __init__(self, model_path: str = "your-username/mhg-pos-bert"):
        self._tokenizer = AutoTokenizer.from_pretrained(model_path)
        self._model = AutoModelForTokenClassification.from_pretrained(model_path)
        self._model.eval()

    @property
    def name(self) -> str:
        return "bert-mhg-pos"

    def predict(self, document: Document) -> list[str]:
        tags = []
        for token in document.mappable_tokens:
            inputs = self._tokenizer(token.form_for_tagging, return_tensors="pt")
            with torch.no_grad():
                logits = self._model(**inputs).logits
            # Prediction for the first real token (skip [CLS])
            label_id = logits[0, 1, :].argmax().item()
            tags.append(LABEL_MAP.get(label_id, "NOM"))
        return tags
```

### CRF Tagger (classical)

A trained CRF model saved as a pickle file:

```python
# crf_tagger.py

import pickle
from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.data.corpus import Document

class CrfTagger(ModelAdapter):
    def __init__(self, model_path: str = "models/mhg_crf.pkl"):
        with open(model_path, "rb") as f:
            self._model = pickle.load(f)

    @property
    def name(self) -> str:
        return "crf-mhg"

    def predict(self, document: Document) -> list[str]:
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

## Before You Run on the Full Corpus

- [ ] Test on 1 document first (`SUBSET_SIZE = 1`) — does it run without errors?
- [ ] Check that the gold passthrough gives 100% accuracy (proves the pipeline works)
- [ ] Verify your model returns only tags from the 16-tag set
- [ ] Verify the tag count matches: `len(result) == len(document.mappable_tokens)`
- [ ] Then increase: `SUBSET_SIZE = 10`, then remove the subset for all 406 documents

## Troubleshooting

| Problem | What to do |
|---------|------------|
| `ValueError: expected N tags, got M` | Your `predict()` returns the wrong number of tags. Make sure you iterate over `document.mappable_tokens`, not `document.tokens`. |
| Tags not recognized in the report | You're returning tags outside the 16-tag set. Add a mapping step from your model's tagset to MHDBDB tags. |
| Model is very slow on full corpus | The full ReM has 2.1M tokens across 406 documents. Start with `SUBSET_SIZE = 3`. For BERT models, consider batching instead of one-word-at-a-time. |
| `ImportError: No module named 'my_tagger'` | Run the script from the same directory where `my_tagger.py` lives: `cd /path/to/repo && python run_my_tagger.py` |
| `FileNotFoundError: No XML files found` | The corpus path is wrong. Run `mhd-bench doctor` to auto-detect it, or check [GETTING-STARTED.md](GETTING-STARTED.md). |
