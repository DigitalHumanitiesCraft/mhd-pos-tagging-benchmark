"""CLI entry point for mhd-bench."""

from __future__ import annotations

import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()

ADAPTER_CHOICES = ["passthrough", "majority", "api", "cli"]
CLI_PRESETS = ["claude", "gemini", "codex", "copilot"]


def _resolve_corpus_dir(corpus_dir: Path | None) -> Path:
    """Resolve corpus directory: use explicit path or auto-detect."""
    if corpus_dir is not None:
        if not corpus_dir.exists():
            raise click.UsageError(f"Corpus directory not found: {corpus_dir}")
        return corpus_dir

    from mhd_pos_benchmark.doctor import find_corpus_dir

    found = find_corpus_dir()
    if found is not None:
        console.print(f"Auto-detected corpus: [bold]{found}[/bold]")
        return found

    raise click.UsageError(
        "Corpus directory not found. Either:\n"
        "  1. Pass it explicitly: mhd-bench evaluate /path/to/cora-xml/\n"
        "  2. Download from: https://www.linguistics.rub.de/rem/access/index.html\n"
        "     Extract so that ReM-v2.1_coraxml/ReM-v2.1_coraxml/cora-xml/*.xml exists"
    )


def _parse_and_map(corpus_dir: Path, subset: int | None = None):
    """Shared helper: parse corpus, map tags, optionally select subset."""
    from mhd_pos_benchmark.data.rem_parser import parse_corpus
    from mhd_pos_benchmark.mapping.tagset_mapper import TagsetMapper

    console.print(f"Parsing corpus from {corpus_dir}...")
    documents = parse_corpus(corpus_dir)
    console.print(f"Parsed {len(documents)} documents")

    mapper = TagsetMapper()
    for doc in documents:
        mapper.map_document(doc)

    if subset is not None:
        from mhd_pos_benchmark.data.subset import describe_subset, select_subset

        documents = select_subset(documents, n=subset)
        console.print("\n[bold]Subset selected:[/bold]")
        if len(documents) < subset:
            console.print(
                f"[yellow]Note: requested {subset} documents, "
                f"got {len(documents)} (genre-stratified sampling)[/yellow]"
            )
        console.print(describe_subset(documents))

    return documents


def _resolve_api_key(api_key: str | None) -> str | None:
    """Resolve API key: prompt interactively, or return the provided value."""
    if api_key == "prompt":
        return click.prompt("API key", hide_input=True)
    return api_key


def _make_adapter(
    name: str,
    documents: list,
    api_key: str | None = None,
    cli_cmd: str | None = None,
    model: str | None = None,
    provider: str | None = None,
    api_base: str | None = None,
    preset: str | None = None,
):
    """Instantiate an adapter by name."""
    if name == "passthrough":
        from mhd_pos_benchmark.adapters.gold_passthrough import GoldPassthroughAdapter

        return GoldPassthroughAdapter()
    elif name == "majority":
        from mhd_pos_benchmark.adapters.majority_class import MajorityClassAdapter

        adapter = MajorityClassAdapter(documents)
        console.print(f"Majority tag: [bold]{adapter.majority_tag}[/bold]")
        return adapter
    elif name == "api":
        from mhd_pos_benchmark.adapters.generic_api import PROVIDERS, GenericApiAdapter

        effective_provider = provider or "openai"
        if model is None:
            default_model = PROVIDERS.get(effective_provider, {}).get("default_model", "gpt-4o")
            console.print(f"No --model specified, using default: [bold]{default_model}[/bold]")
        return GenericApiAdapter(
            provider=effective_provider,
            model=model,
            api_key=api_key,
            api_base=api_base,
        )
    elif name == "cli":
        from mhd_pos_benchmark.adapters.generic_cli import GenericCliAdapter

        if preset:
            console.print(f"Using CLI preset: [bold]{preset}[/bold]")
            return GenericCliAdapter(preset=preset, model=model, model_name=model)
        elif cli_cmd:
            return GenericCliAdapter(cli_cmd=cli_cmd, model_name=model)
        else:
            raise click.UsageError(
                "--adapter cli requires --preset or --cli-cmd.\n"
                f"  Presets: {', '.join(CLI_PRESETS)}\n"
                "  Example: --adapter cli --preset claude --model opus\n"
                "  Example: --adapter cli --cli-cmd \"my-tool --flag\""
            )
    else:
        # Smart suggestions for common mistakes
        suggestions = {
            "gemini": "--adapter api --provider gemini  or  --adapter cli --preset gemini",
            "openai": "--adapter api --provider openai",
            "mistral": "--adapter api --provider mistral",
            "groq": "--adapter api --provider groq",
            "claude": "--adapter cli --preset claude",
            "codex": "--adapter cli --preset codex",
            "copilot": "--adapter cli --preset copilot",
            "gpt-4o": "--adapter api --provider openai --model gpt-4o",
            "gpt": "--adapter api --provider openai",
            "opus": "--adapter cli --preset claude --model opus",
            "sonnet": "--adapter cli --preset claude --model sonnet",
            "llama": "--adapter api --api-base http://localhost:11434/v1 --model llama3",
        }
        hint = suggestions.get(name.lower(), "")
        msg = f"Unknown adapter: {name}. Valid adapters: {', '.join(ADAPTER_CHOICES)}."
        if hint:
            msg += f"\n  Did you mean: {hint}"
        msg += "\n  Run 'mhd-bench doctor' to see available tools."
        raise click.UsageError(msg)


@click.group()
@click.version_option(package_name="mhd-pos-benchmark")
def cli() -> None:
    """MHD POS Tagging Benchmark — evaluate POS taggers against ReM ground truth."""


@cli.command()
@click.argument("corpus_dir", type=click.Path(path_type=Path), default=None, required=False)
@click.option("--stats", is_flag=True, help="Show corpus statistics")
def parse(corpus_dir: Path | None, stats: bool) -> None:
    """Parse ReM CORA-XML files and optionally show statistics."""
    from mhd_pos_benchmark.data.rem_parser import parse_corpus

    corpus_dir = _resolve_corpus_dir(corpus_dir)
    documents = parse_corpus(corpus_dir)
    console.print(f"Parsed {len(documents)} documents")

    if stats:
        total_tokens = sum(len(d.tokens) for d in documents)
        table = Table(title="Corpus Statistics")
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")
        table.add_row("Documents", str(len(documents)))
        table.add_row("Total tokens (tok_anno)", str(total_tokens))
        table.add_row(
            "Avg tokens/document",
            f"{total_tokens / len(documents):.0f}" if documents else "0",
        )

        pos_counts: dict[str, int] = {}
        for doc in documents:
            for token in doc.tokens:
                pos_counts[token.pos_hits] = pos_counts.get(token.pos_hits, 0) + 1

        table.add_row("Unique HiTS tags", str(len(pos_counts)))
        console.print(table)

        tag_table = Table(title="\nTop 20 HiTS Tags")
        tag_table.add_column("Tag", style="bold")
        tag_table.add_column("Count", justify="right")
        tag_table.add_column("%", justify="right")
        for tag, count in sorted(pos_counts.items(), key=lambda x: -x[1])[:20]:
            tag_table.add_row(tag, str(count), f"{count / total_tokens:.1%}")
        console.print(tag_table)


@cli.command()
@click.option(
    "--corpus-dir",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Corpus directory (for --validate)",
)
@click.option("--validate", is_flag=True, help="Check all corpus tags have mappings")
def mapping(corpus_dir: Path | None, validate: bool) -> None:
    """Show or validate the HiTS -> MHDBDB tagset mapping."""
    from mhd_pos_benchmark.mapping.tagset_mapper import TagsetMapper

    mapper = TagsetMapper()

    if validate:
        from mhd_pos_benchmark.data.rem_parser import parse_corpus

        corpus_dir = _resolve_corpus_dir(corpus_dir)
        documents = parse_corpus(corpus_dir)
        unmapped = mapper.find_unmapped(documents)

        if unmapped:
            console.print(f"[red]Found {len(unmapped)} unmapped HiTS tags:[/red]")
            for tag, count in unmapped.items():
                console.print(f"  {tag}: {count} occurrences")
            raise SystemExit(1)
        else:
            console.print("[green]All HiTS tags in corpus have mappings.[/green]")
    else:
        table = Table(title="HiTS -> MHDBDB Mapping")
        table.add_column("HiTS", style="bold")
        table.add_column("MHDBDB")
        for hits, mhdbdb in sorted(mapper.mappings.items()):
            table.add_row(hits, str(mhdbdb) if mhdbdb else "[dim]excluded[/dim]")
        console.print(table)


@cli.command()
@click.argument("corpus_dir", type=click.Path(path_type=Path), default=None, required=False)
@click.option(
    "--adapter",
    type=click.Choice(ADAPTER_CHOICES),
    default="passthrough",
    help="Model adapter to use",
)
@click.option(
    "--subset",
    type=int,
    default=None,
    help="Evaluate on N representative documents (for prototyping)",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Save JSON results to this path",
)
@click.option(
    "--api-key",
    type=str,
    default=None,
    is_flag=False,
    flag_value="prompt",
    help="API key for the adapter. Pass a value, or use bare --api-key to enter interactively (masked).",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
@click.option(
    "--continue-on-error",
    is_flag=True,
    help="Skip documents that fail instead of aborting the run",
)
@click.option(
    "--cli-cmd",
    type=str,
    default=None,
    help="CLI command for --adapter cli (e.g. 'gemini -p', 'codex exec', 'copilot -p -s').",
)
@click.option(
    "--model",
    "model_name",
    type=str,
    default=None,
    help="Model name for display/caching (e.g. 'gpt-4o', 'gemini-2.5-pro').",
)
@click.option(
    "--provider",
    type=click.Choice(["openai", "gemini", "mistral", "groq"]),
    default=None,
    help="API provider for --adapter api (default: openai).",
)
@click.option(
    "--api-base",
    type=str,
    default=None,
    help="Custom API base URL (e.g. 'http://localhost:11434/v1' for ollama).",
)
@click.option(
    "--preset",
    type=str,
    default=None,
    help="CLI preset for --adapter cli (claude, gemini, codex, copilot). Knows flags, output format, etc.",
)
def evaluate(
    corpus_dir: Path | None,
    adapter: str,
    subset: int | None,
    output: Path | None,
    api_key: str | None,
    verbose: bool,
    continue_on_error: bool,
    cli_cmd: str | None,
    model_name: str | None,
    provider: str | None,
    api_base: str | None,
    preset: str | None,
) -> None:
    """Run evaluation pipeline on the corpus."""
    from rich.progress import Progress

    from mhd_pos_benchmark.evaluation.comparator import align_corpus
    from mhd_pos_benchmark.evaluation.metrics import compute_metrics
    from mhd_pos_benchmark.evaluation.report import print_report, save_json

    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    corpus_dir = _resolve_corpus_dir(corpus_dir)
    api_key = _resolve_api_key(api_key)
    documents = _parse_and_map(corpus_dir, subset)
    model = _make_adapter(
        adapter, documents, api_key=api_key, cli_cmd=cli_cmd, model=model_name,
        provider=provider, api_base=api_base, preset=preset,
    )

    console.print(f"\nRunning evaluation with adapter: [bold]{model.name}[/bold]...")
    with Progress(console=console) as progress:
        task = progress.add_task("Evaluating", total=len(documents))
        alignments = align_corpus(
            documents, model,
            continue_on_error=continue_on_error,
            progress_callback=lambda: progress.advance(task),
        )
    result = compute_metrics(alignments, model.name)

    print_report(result, console)

    if output:
        save_json(result, output)
        console.print(f"\nResults saved to {output}")


@cli.command()
@click.argument("corpus_dir", type=click.Path(path_type=Path), default=None, required=False)
@click.option(
    "--adapters",
    type=str,
    default=None,
    help="Comma-separated adapter names to run live (e.g. 'passthrough,majority').",
)
@click.option(
    "--models",
    type=str,
    default=None,
    help="Comma-separated model names to compare from cache (e.g. 'claude-opus-4.6,gemini-2.5-pro').",
)
@click.option(
    "--subset",
    type=int,
    default=None,
    help="Evaluate on N representative documents",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Save JSON comparison to this path",
)
@click.option(
    "--api-key",
    type=str,
    default=None,
    is_flag=False,
    flag_value="prompt",
    help="API key for API-based adapters. Pass a value, or use bare --api-key to enter interactively (masked).",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
@click.option(
    "--continue-on-error",
    is_flag=True,
    help="Skip documents that fail instead of aborting the run",
)
@click.option(
    "--cli-cmd",
    type=str,
    default=None,
    help="CLI command for 'cli' adapter entries (e.g. 'gemini -p').",
)
@click.option(
    "--model",
    "model_name",
    type=str,
    default=None,
    help="Model name for display/caching.",
)
@click.option(
    "--provider",
    type=click.Choice(["openai", "gemini", "mistral", "groq"]),
    default=None,
    help="API provider for 'api' adapter entries.",
)
@click.option(
    "--api-base",
    type=str,
    default=None,
    help="Custom API base URL.",
)
@click.option(
    "--preset",
    type=str,
    default=None,
    help="CLI preset for 'cli' adapter entries (claude, gemini, codex, copilot).",
)
def compare(
    corpus_dir: Path | None,
    adapters: str | None,
    models: str | None,
    subset: int | None,
    output: Path | None,
    api_key: str | None,
    verbose: bool,
    continue_on_error: bool,
    cli_cmd: str | None,
    model_name: str | None,
    provider: str | None,
    api_base: str | None,
    preset: str | None,
) -> None:
    """Compare multiple models side-by-side.

    Two modes:

    \b
    1. --models: Compare cached results from previous evaluate runs (recommended).
       mhd-bench compare corpus/ --models claude-opus-4.6,gemini-2.5-pro

    \b
    2. --adapters: Run adapters live and compare (for baselines or single-config adapters).
       mhd-bench compare corpus/ --adapters passthrough,majority

    Both flags can be combined to mix cached and live results.
    """
    import json

    from rich.progress import Progress

    from mhd_pos_benchmark.evaluation.comparator import align_corpus
    from mhd_pos_benchmark.evaluation.metrics import EvaluationResult, compute_metrics
    from mhd_pos_benchmark.evaluation.report import print_report

    if not adapters and not models:
        raise click.UsageError("Provide --adapters, --models, or both.")

    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    corpus_dir = _resolve_corpus_dir(corpus_dir)
    api_key = _resolve_api_key(api_key)
    documents = _parse_and_map(corpus_dir, subset)

    results: list[EvaluationResult] = []

    # 1. Cached models (from previous evaluate runs)
    if models:
        from mhd_pos_benchmark.adapters.cached import CachedAdapter

        model_names = [m.strip() for m in models.split(",")]
        for mname in model_names:
            try:
                cached_adapter = CachedAdapter(mname)
            except FileNotFoundError as e:
                raise click.UsageError(str(e)) from e
            console.print(f"\nLoading cached results: [bold]{mname}[/bold]...")
            with Progress(console=console) as progress:
                task = progress.add_task(f"Loading {mname}", total=len(documents))
                alignments = align_corpus(
                    documents, cached_adapter,
                    continue_on_error=continue_on_error,
                    progress_callback=lambda: progress.advance(task),
                )
            result = compute_metrics(alignments, mname)
            results.append(result)
            print_report(result, console)

    # 2. Live adapters (baselines or single-config)
    if adapters:
        adapter_names = [a.strip() for a in adapters.split(",")]
        for name in adapter_names:
            model = _make_adapter(
                name, documents, api_key=api_key, cli_cmd=cli_cmd, model=model_name,
                provider=provider, api_base=api_base, preset=preset,
            )
            console.print(f"\nRunning: [bold]{model.name}[/bold]...")
            with Progress(console=console) as progress:
                task = progress.add_task(f"Evaluating {model.name}", total=len(documents))
                alignments = align_corpus(
                    documents, model,
                    continue_on_error=continue_on_error,
                    progress_callback=lambda: progress.advance(task),
                )
            result = compute_metrics(alignments, model.name)
            results.append(result)
            print_report(result, console)

    # Side-by-side summary
    console.print("\n[bold]Comparison Summary[/bold]\n")
    cmp_table = Table(title="Head-to-Head")
    cmp_table.add_column("Metric", style="bold")
    for r in results:
        cmp_table.add_column(r.adapter_name, justify="right")

    cmp_table.add_row("Accuracy", *[f"{r.accuracy:.4f}" for r in results])
    cmp_table.add_row("Macro-F1", *[f"{r.macro_f1:.4f}" for r in results])
    cmp_table.add_row("Micro-F1", *[f"{r.micro_f1:.4f}" for r in results])
    cmp_table.add_row("Evaluated tokens", *[str(r.evaluated_tokens) for r in results])
    console.print(cmp_table)

    # Per-tag comparison
    all_tags = sorted({tm.tag for r in results for tm in r.per_tag})
    tag_table = Table(title="\nPer-Tag F1 Comparison")
    tag_table.add_column("Tag", style="bold")
    for r in results:
        tag_table.add_column(r.adapter_name, justify="right")

    for tag in all_tags:
        row = [tag]
        for r in results:
            f1 = next((tm.f1 for tm in r.per_tag if tm.tag == tag), 0.0)
            row.append(f"{f1:.4f}")
        tag_table.add_row(*row)
    console.print(tag_table)

    if output:
        comparison = {
            "adapters": [
                {
                    "name": r.adapter_name,
                    "accuracy": r.accuracy,
                    "macro_f1": r.macro_f1,
                    "micro_f1": r.micro_f1,
                    "evaluated_tokens": r.evaluated_tokens,
                }
                for r in results
            ]
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)
        console.print(f"\nComparison saved to {output}")


@cli.command()
def doctor() -> None:
    """Check prerequisites, detect available tools, suggest next steps."""
    from mhd_pos_benchmark.doctor import (
        check_api_keys,
        check_cache_status,
        check_cli_tools,
        check_corpus,
        check_openai_sdk,
        check_python_version,
        suggest_commands,
    )

    console.print("\n[bold]MHD POS Tagging Benchmark — System Check[/bold]\n")

    # Core checks
    for check in [check_python_version(), check_corpus(), check_openai_sdk()]:
        icon = {"ok": "[green]OK[/green]", "warn": "[yellow]WARN[/yellow]", "fail": "[red]FAIL[/red]"}[check.status]
        console.print(f"  {icon:>16s}  {check.name}: {check.message}")
        if check.fix_hint:
            for line in check.fix_hint.splitlines():
                console.print(f"           {line}")

    # CLI tools (compact)
    cli_results = check_cli_tools()
    cli_line = "  CLI Tools:  " + "  ".join(
        f"{r.name} [green]\u2713[/green]" if r.status == "ok" else f"{r.name} [dim]\u2717[/dim]"
        for r in cli_results
    )
    console.print(f"\n{cli_line}")

    # API keys (compact)
    api_results = check_api_keys()
    api_line = "  API Keys:   " + "  ".join(
        f"{r.name} [green]\u2713[/green]" if r.status == "ok" else f"{r.name} [dim]\u2717[/dim]"
        for r in api_results
    )
    console.print(api_line)

    # Cache status
    cache_results = check_cache_status()
    if cache_results:
        cache_line = "  Cache:      " + ", ".join(f"{r.name} ({r.message})" for r in cache_results)
        console.print(f"\n{cache_line}")

    # Suggestions
    corpus_ok = check_corpus().status == "ok"
    suggestions = suggest_commands(cli_results, api_results, cache_results, corpus_ok)
    if suggestions:
        console.print("\n  [bold]Suggested next steps:[/bold]\n")
        for suggestion in suggestions:
            for line in suggestion.splitlines():
                console.print(f"    {line}")
            console.print()
