# Getting Started

From zero to your first benchmark result in about 15 minutes. No programming experience required: just a terminal and a few commands.

## Prerequisites

- **Python 3.13+.** Older versions will not work.
- **A terminal** (macOS: Terminal.app or iTerm; Windows: PowerShell; Linux: any terminal).
- **~200 MB free disk space** for the ReM corpus and installed packages.

### Check your Python version

```bash
python3 --version
```

You should see something like `Python 3.13.2`. If not:

- **macOS:** `brew install python@3.13` (requires [Homebrew](https://brew.sh))
- **Windows:** Download from [python.org](https://www.python.org/downloads/). Enable "Add Python to PATH" during installation.
- **Linux:** `sudo apt install python3.13` (Ubuntu/Debian) or your distro's equivalent.

If `python3` doesn't work, try `python`. This guide uses `python3` throughout; substitute as needed.

## Step 1: Install the benchmark

```bash
git clone https://github.com/DigitalHumanitiesCraft/mhd-pos-tagging-benchmark.git
cd mhd-pos-tagging-benchmark
pip install -e ".[dev]"
```

This installs the `mhd-bench` command and all dependencies. The `[dev]` part adds testing tools (small footprint, no harm in including them).

Verify:

```bash
mhd-bench --version
```

If you see a version number (e.g. `0.1.0`), the installation worked.

**If `pip` fails:** Some systems need `pip3` instead, or `python3 -m pip install -e ".[dev]"`.

## Step 2: Download the ReM corpus

The benchmark evaluates against the Referenzkorpus Mittelhochdeutsch (ReM). The corpus data is not included in the repository (106 MB, gitignored). You need to download it once.

1. Go to https://www.linguistics.rub.de/rem/access/index.html
2. Download the **CORA-XML** version
3. Extract the archive **inside the benchmark folder** (next to `README.md`)

After extraction, your folder structure should look like this:

```
mhd-pos-tagging-benchmark/
├── README.md
├── ReM-v2.1_coraxml/
│   └── ReM-v2.1_coraxml/
│       └── cora-xml/
│           ├── M001-N1.xml
│           ├── M002-N1.xml
│           └── ... (406 XML files)
└── src/
```

The doubled folder name (`ReM-v2.1_coraxml/ReM-v2.1_coraxml/`) comes from the archive format. That's expected.

Verify the files are in place:

```bash
ls ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/*.xml | head -3
```

You should see three XML filenames. If you get an error, check that you're in the right directory (`cd mhd-pos-tagging-benchmark`) and that the path matches.

## Step 3: Parse the corpus

Test whether the benchmark can read the ReM data:

```bash
mhd-bench parse ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ --stats
```

Output:

```
Parsed 406 documents

        Corpus Statistics
┌──────────────────────┬───────────┐
│ Metric               │     Value │
├──────────────────────┼───────────┤
│ Documents            │       406 │
│ Total tokens         │ 2,579,276 │
│ Avg tokens/document  │     6,352 │
│ Unique HiTS tags     │        73 │
└──────────────────────┴───────────┘
```

Below the summary you'll see a list of the most frequent POS tags. 406 documents, 2.58 million tokens: that's the full corpus.

## Step 4: Sanity check

Before testing a real model, verify that the entire processing pipeline works. The "gold passthrough" adapter returns the correct tags from the corpus. It must produce 100% accuracy; if it doesn't, something is wrong with the pipeline.

```bash
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter passthrough \
  --subset 3
```

`--subset 3` picks three representative documents (instead of all 406). That's enough for a sanity check.

The output should contain:

```
│ Accuracy         │       1.0000 │
│ Macro-F1         │       1.0000 │
```

1.0000 = 100% correct. The pipeline works.

## Step 5: Test your first model

You can test any LLM you have access to. Two common paths:

### Option A: CLI tool (e.g. Claude, Antigravity)

If you have a CLI tool installed (`claude`, `agy`, `codex`, `copilot`):

```bash
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter cli \
  --preset claude \
  --model claude-opus-5 \
  --subset 1
```

What the flags mean:

- `--adapter cli` tells the benchmark to use a CLI tool
- `--preset claude` selects the built-in configuration for that tool: which flags
  it needs, how it takes a system prompt, how its output is parsed, and that it
  must run in an empty directory so it cannot read your project files
- `--model claude-opus-5` is both the model requested and the name under which
  results are stored. Use a full version, not an alias like `opus`: aliases move
  to a new model every few months, and then a cached result no longer says which
  model produced it.
- `--subset 1` tests only one document (fast and cheap for a first try)

Available presets: `claude`, `antigravity`, `gemini`, `codex`, `copilot`. If your
tool is not among them, use `--cli-cmd "your-tool --flags"` instead. Run
`mhd-bench doctor` to see which of them are installed.

**Take the model name from the tool, not from a model announcement.** Each CLI
has its own naming, and it is usually not the API model ID. A name that the tool
does not know is rejected right away, which is harmless, but the reverse mistake
costs more: concluding that a model is unavailable when only the spelling was
wrong. Where to look:

| Preset | How to see the available models |
|---|---|
| `claude` | `--model` takes an alias (`opus`, `sonnet`) or a full ID like `claude-opus-5` |
| `antigravity` | `agy models` prints ID and display name; the ID is the left column |
| `codex` | `~/.codex/models_cache.json`, or `/model` in the interactive TUI |
| `copilot` | `/model` in the interactive TUI |

Two notes on availability, current as of August 2026: Gemini CLI stopped serving
consumer accounts on 18 June 2026 and now needs a paid `GEMINI_API_KEY`, so
Option B is the easier route for Gemini. Its successor is the Antigravity CLI
(`agy`), available through the `antigravity` preset.

### Option B: API with key (e.g. OpenAI, Gemini API)

If you have an API key:

```bash
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter api \
  --provider gemini \
  --model gemini-3.1-pro-preview \
  --api-key \
  --subset 1
```

The bare `--api-key` (no value) prompts for the key interactively: it won't be displayed as you type. You can also pass it directly (`--api-key AI...`), but the interactive variant is safer because the key won't end up in your shell history.

### Reading the results

After the run, you'll see a table like this:

```
                Summary
┌──────────────────┬──────────────┐
│ Documents        │            1 │
│ Total tokens     │           20 │
│ Evaluated tokens │           13 │
│ Excluded tokens  │   7 (35.0%)  │
│ Accuracy         │       0.9231 │
│ Macro-F1         │       0.9048 │
└──────────────────┴──────────────┘
```

- **Evaluated tokens:** Only tokens with a valid POS tag are scored. Punctuation, foreign material, and ambiguous conjunctions (KO\*) are excluded.
- **Accuracy:** Fraction of correctly tagged tokens (here: 12 out of 13 = 92.3%).
- **Macro-F1:** Average F1 across all tags (weights every tag equally, including rare ones).

Below the summary, a per-tag table shows Precision, Recall, and F1 for each word class.

## Step 6: Save results

Add `--output` to write results as JSON:

```bash
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter cli \
  --preset claude \
  --model claude-opus-5 \
  --subset 3 \
  --output results/claude-opus-5.json
```

The JSON file contains accuracy, per-tag metrics, and the full confusion matrix. You can process it further in Python, R, or any other tool.

## Step 7: Compare two models

This is the core use case — "Which model tags MHG better?" The workflow is: evaluate each model separately (results are cached), then compare.

### Run each model

```bash
# Model 1: Claude Opus 5 (via CLI subscription)
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter cli \
  --preset claude \
  --model claude-opus-5 \
  --subset 3

# Model 2: Gemini 3.1 Pro (via API key)
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter api \
  --provider gemini \
  --model gemini-3.1-pro-preview \
  --api-key \
  --subset 3
```

Each run takes a few minutes (depending on the model and document sizes). Results are cached automatically in `results/<model-name>/` — if you run the same command again, it finishes instantly.

### Compare the results

```bash
mhd-bench compare ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --models claude-opus-5,gemini-3.1-pro-preview \
  --subset 3
```

This loads the cached predictions (no new API calls) and produces a side-by-side table:

```
              Head-to-Head
┌──────────────────┬─────────────────┬────────────────────────┐
│ Metric           │ claude-opus-5   │ gemini-3.1-pro-preview │
├──────────────────┼─────────────────┼────────────────────────┤
│ Accuracy         │          0.9231 │       0.8846 │
│ Macro-F1         │          0.9048 │       0.8512 │
│ Micro-F1         │          0.9231 │       0.8846 │
│ Evaluated tokens │             780 │          780 │
└──────────────────┴─────────────────┴──────────────┘
```

Below that, a per-tag F1 comparison shows which word classes each model handles better.

### Tips for meaningful comparisons

- **Same documents:** Every model must be scored on the same texts, otherwise the numbers in the table describe different things. `compare` warns you when that happened, but it can only warn after the fact.
- **Pin the selection for anything you publish.** `--subset 3` picks three documents by sampling, and the sample moves when the corpus or the sampling code changes. Each `--subset` run therefore prints the equivalent `--documents` line; copy it into your notes and use it from then on:

```bash
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter cli --preset claude --model claude-opus-5 \
  --documents M033,M174,M040
```

  The saved JSON also records `document_ids`, so an old result can always tell you what it covered.
- **Start small:** `--subset 3` for quick tests, `--subset 10` for paper-worthy results, no `--subset` for the full 406-document corpus.
- **Add baselines:** The `majority` adapter (most frequent tag for every token) gives you a lower bound. Run it once and include it in your comparison:

```bash
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter majority --subset 3

mhd-bench compare ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --models majority-class,claude-opus-5,gemini-3.1-pro-preview \
  --subset 3
```

### Where results are stored

```
results/
├── claude-opus-5/
│   └── predictions.jsonl       ← cached predictions, one line per document
├── gemini-3.1-pro-preview/
│   └── predictions.jsonl
└── majority-class/
    └── predictions.jsonl
```

These caches are gitignored (local only). Delete a model's folder to force re-evaluation:

```bash
rm -rf results/claude-opus-5/    # next evaluate run will re-tag everything
```

## Going further

- **More models:** You can compare as many models as you want. Just `evaluate` each one, then list them all in `compare --models a,b,c,d`.
- **Save as JSON:** Add `--output results/comparison.json` to any `evaluate` command for machine-readable results with confusion matrices.
- **Custom models:** If you have a BERT, CRF, or other tagger with Python bindings, see the [Model Adapter Guide](MODEL-ADAPTER-GUIDE.md).
- **Full CLI reference:** Run `mhd-bench evaluate --help` or `mhd-bench compare --help` for all available flags.

## Problems?

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common errors and their solutions.
