# Troubleshooting

Common problems and their fixes, ordered by when they typically occur: Installation → Corpus → Evaluation → Results.

## Installation

### `pip install` fails with "requires Python >=3.13"

Your Python version is too old.

```bash
python3 --version
# If < 3.13: upgrade
```

- macOS: `brew install python@3.13`
- Windows: Install from [python.org](https://www.python.org/downloads/)
- Linux: `sudo apt install python3.13` or via [pyenv](https://github.com/pyenv/pyenv)

If you have multiple Python versions, try `python3.13 -m pip install -e ".[dev]"` directly.

### `mhd-bench: command not found`

`pip install` succeeded, but the install directory isn't on your PATH.

Three fixes:

1. **Call directly:** `python3 -m mhd_pos_benchmark.cli` instead of `mhd-bench`
2. **Check PATH:** `pip install` sometimes prints "WARNING: The script mhd-bench is installed in '/Users/you/.local/bin' which is not on PATH". Add that directory to your PATH.
3. **Use a virtual environment:** `python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`. Inside the venv, `mhd-bench` is always available.

### `ModuleNotFoundError: No module named 'lxml'`

Dependencies weren't installed. Likely `pip install` was run without `-e ".[dev]"`, or in a different Python environment.

```bash
pip install -e ".[dev]"
```

If that doesn't help: check with `which python3` and `which pip` that both point to the same Python installation.

## Corpus

### `FileNotFoundError: No XML files found in ...`

The corpus path is wrong. Most common mistake: the nested folder structure after extraction.

```bash
# Correct:
ls ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/*.xml | head -3

# Common mistake – one level too few:
ls ReM-v2.1_coraxml/cora-xml/*.xml       # does NOT work

# Common mistake – wrong directory:
ls cora-xml/*.xml                          # does NOT work
```

If you extracted the archive differently, adjust the path in your commands. The benchmark needs the directory that directly contains the `.xml` files.

### `lxml.etree.XMLSyntaxError` during parsing

One of the XML files is corrupted, likely from an incomplete extraction.

1. Delete the corpus folder
2. Re-download the archive
3. Extract again

If the error names a specific file, you can remove just that file and use the rest.

### `Parsed 0 documents` or far fewer than 406

You're pointing at the wrong directory, or the XML files have an unexpected extension.

```bash
# How many XML files are there?
ls ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/*.xml | wc -l
# Expected: 406
```

0 = wrong path. Fewer than 406 = incomplete extraction.

## Evaluation

### `Unknown adapter: gemini` (or `claude`, `gpt`, etc.)

Model names are not adapter names. There are four adapters: `passthrough`, `majority`, `api`, `cli`.

For LLMs, use `--adapter api` or `--adapter cli` and specify the model name separately:

```bash
# Wrong:
mhd-bench evaluate corpus/ --adapter gemini

# Correct (API):
mhd-bench evaluate corpus/ --adapter api --provider gemini --model gemini-3.1-pro-preview --api-key

# Correct (CLI):
mhd-bench evaluate corpus/ --adapter cli --preset gemini --model gemini-3.1-pro-preview
```

The benchmark shows a hint with the correct command when you use a known model name as an adapter name.

### `--adapter cli requires --preset or --cli-cmd`

You chose `--adapter cli` but didn't specify which CLI tool to call.

```bash
# Preferred: a preset knows the tool's flags and isolation settings
mhd-bench evaluate corpus/ \
  --adapter cli \
  --preset claude \
  --model claude-opus-5

# Fallback for tools without a preset
mhd-bench evaluate corpus/ \
  --adapter cli \
  --cli-cmd "my-tagger --stdin" \
  --model my-tagger-v1
```

Presets: `claude`, `antigravity`, `gemini`, `codex`, `copilot`.

### `IneligibleTierError` from Gemini CLI

Google stopped serving consumer accounts through Gemini CLI on 18 June 2026. An
OAuth login now fails with "This client is no longer supported for Gemini Code
Assist for individuals".

Three ways forward:

```bash
# 1. Use the Gemini API instead (needs a key from aistudio.google.com)
mhd-bench evaluate corpus/ --adapter api --provider gemini \
  --model gemini-3.1-pro-preview --api-key

# 2. Use the successor CLI
mhd-bench evaluate corpus/ --adapter cli --preset antigravity

# 3. Keep Gemini CLI with a paid API key in GEMINI_API_KEY
```

### The model seems to know about this benchmark

Coding CLIs read instruction files (CLAUDE.md, AGENTS.md, GEMINI.md) from their
working directory, which would let the tagger see the benchmark's own
documentation. The presets prevent this by running the tool in an empty
directory with tools and MCP servers switched off.

If you built your own invocation with `--cli-cmd`, you do not get that
protection. Either switch to a preset, or add the equivalent flags for your tool.

### `CLI tool 'claude' not found on PATH`

The CLI tool isn't installed or isn't on your PATH.

Check whether you can call it directly:

```bash
which claude      # macOS/Linux
where claude      # Windows
```

If nothing is found: install the tool (e.g. `npm install -g @anthropic-ai/claude-code` for Claude). If it's installed but not found: open a new terminal window (PATH is loaded at startup).

### `No API key provided. Use --api-key or set GEMINI_API_KEY.`

The API adapter needs a key and can't find one.

Three ways to provide it:

```bash
# 1. Interactive (safest – key is not displayed):
mhd-bench evaluate corpus/ --adapter api --provider gemini --api-key

# 2. Inline:
mhd-bench evaluate corpus/ --adapter api --provider gemini --api-key AIza...

# 3. Environment variable (auto-detected):
export GEMINI_API_KEY=AIza...
mhd-bench evaluate corpus/ --adapter api --provider gemini
```

Environment variable names per provider: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `GROQ_API_KEY`.

### `ImportError: The 'openai' package is required for --adapter api`

The optional API dependency is missing.

```bash
pip install mhd-pos-benchmark[api]
# or:
pip install openai
```

### `Failed after 3 attempts: Expected 47 tags, got 45`

The LLM returned a different number of tags than there were tokens in the chunk. This happens occasionally with long documents or weaker models.

Possible fixes:

- **Smaller chunks:** `--chunk-size 100` gives the model less to keep aligned per call. This is the most direct fix, at the price of more calls.
- **Stronger model:** Frontier models (Claude Opus 5, Gemini 3.1 Pro, GPT-5.6) hold the count reliably; smaller ones drift.
- **Add `--continue-on-error`:** The benchmark skips the failed document and continues. Note that the run then covers fewer documents than the others it will be compared against, and `compare` will warn about it.

Note that `--chunk-size` is part of the cache key, so changing it re-runs everything for that model.

### Evaluation runs but is extremely slow

Possible causes:

- **Full corpus without subset:** 406 documents × LLM calls takes hours. Start with `--subset 3`.
- **Rate limiting:** Some APIs cap requests per minute. The benchmark waits between retries automatically, but throughput suffers.
- **Local model (Ollama etc.):** Speed depends on your GPU. On CPU, a single document can take minutes.

## Results and Cache

### I changed the prompt but results are the same

The cache detects changes to prompt text, chunk size, and temperature automatically via a config hash. If your change still isn't picked up, delete the cache directory for the model in question.

```bash
# Delete cache for one model:
rm -rf results/claude-opus-5/

# Delete all caches:
rm -rf results/
```

The next run will re-tag all documents.

### `Document M106 not found in cache for '<model>'`

`compare --models` reads predictions that an earlier `evaluate` run stored. This
error means the current document selection includes a text that run never saw.

Usually the cause is that `--subset` sampled differently than it did back then:
the sample depends on the corpus and on the sampling code, so it moves. Ask
`mhd-bench doctor` which documents your caches share, and name them:

```bash
mhd-bench compare --models model-a,model-b --documents M033,M174,M040
```

Use `--documents` from the start for anything you plan to publish. Every
`--subset` run prints the matching `--documents` line, and every saved JSON
result lists the `document_ids` it covered.

### `Warning: these models were not scored on the same documents`

Two accuracy numbers side by side only mean something if they describe the same
texts. This warning says they don't, usually after a run with
`--continue-on-error`. The message lists which documents are not shared and
prints the `--documents` line for the common set. Re-run with that line before
reporting the numbers.

### `--subset 5` returns only 3 documents

This is by design. Subset selection distributes documents proportionally across genres (Vers, Prosa, mixed). When there are few documents in some genres, the result can be smaller than requested. The benchmark shows a yellow note:

```
Note: requested 5 documents, got 3 (genre-stratified sampling)
```

The results are still usable: they cover all available genres.

### Accuracy is exactly 1.0000 – is that correct?

Only with `--adapter passthrough`. The gold passthrough returns the correct tags directly; it tests the pipeline, not a model. If a real model shows 100%, check with `-v` (verbose) whether results are coming from cache. The cache might have been populated by a passthrough run that used the same model name.

### The JSON file doesn't seem to contain a confusion matrix

Check the path within the JSON: the confusion matrix is at `confusion_matrix.matrix`.

```json
{
  "adapter": "claude-opus-5",
  "summary": { "accuracy": 0.9231, "..." : "..." },
  "per_tag": [ "..." ],
  "confusion_matrix": {
    "labels": ["ADJ", "ADV", "CCNJ", "..."],
    "matrix": [[45, 2, 0, "..."], "..."]
  }
}
```

Rows = gold tags, columns = predicted tags. `matrix[i][j]` = how often gold tag `labels[i]` was predicted as `labels[j]`.

## Windows-Specific

### `'mhd-bench' is not recognized as an internal or external command`

Same issue as `command not found` on macOS/Linux. Either:

- Use `python -m mhd_pos_benchmark.cli` instead of `mhd-bench`
- Or check whether Python's Scripts folder is on PATH (typically: `C:\Users\YourName\AppData\Local\Programs\Python\Python313\Scripts`)

### Paths with backslashes

The benchmark accepts both `/` and `\` in paths. If you copy-paste from File Explorer, either replace `\` with `/` or wrap the path in quotes:

```bash
mhd-bench parse "ReM-v2.1_coraxml\ReM-v2.1_coraxml\cora-xml"
```

## Still stuck?

1. Add `-v` to your command for debug logging.
2. Check whether the problem reproduces with `--subset 1`. This narrows down whether it's a corpus issue or a model issue.
3. Open a GitHub issue with: the full command, the full error message, and the output of `mhd-bench --version` and `python3 --version`.
