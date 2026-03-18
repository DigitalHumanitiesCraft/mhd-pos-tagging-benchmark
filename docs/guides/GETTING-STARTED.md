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

### Option A: CLI tool (e.g. Claude, Gemini CLI)

If you have a CLI tool installed (e.g. `claude` or `gemini`):

```bash
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter cli \
  --cli-cmd "claude -p --model opus" \
  --model claude-opus-4.6 \
  --subset 1
```

What the flags mean:

- `--adapter cli` tells the benchmark to use a CLI tool
- `--cli-cmd "claude -p --model opus"` is the command to invoke
- `--model claude-opus-4.6` is the name under which results are stored and displayed
- `--subset 1` tests only one document (fast and cheap for a first try)

### Option B: API with key (e.g. OpenAI, Gemini API)

If you have an API key:

```bash
mhd-bench evaluate ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/ \
  --adapter api \
  --provider gemini \
  --model gemini-2.5-pro \
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
  --cli-cmd "claude -p --model opus" \
  --model claude-opus-4.6 \
  --subset 3 \
  --output results/claude-opus-4.6.json
```

The JSON file contains accuracy, per-tag metrics, and the full confusion matrix. You can process it further in Python, R, or any other tool.

## Next steps

- **More documents:** Increase `--subset` gradually (5, 10, 50). Results stabilize with more data, but API costs rise.
- **Caching:** Re-running the same command reuses previously tagged documents. You can run `--subset 10`, then later `--subset 20`: the first 10 come from cache.
- **Compare models:** Run `evaluate` for each model separately, then use `compare` for a side-by-side table. See the README for details.
- **Custom models:** If you have a BERT, CRF, or other tagger, see the [Model Adapter Guide](MODEL-ADAPTER-GUIDE.md).

## Problems?

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common errors and their solutions.
