"""CLI entry point for mhd-bench."""

from __future__ import annotations

import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()

ADAPTER_CHOICES = ["passthrough", "majority", "gemini", "claude-cli"]


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
        console.print(describe_subset(documents))

    return documents


def _resolve_api_key(api_key: str | None) -> str | None:
    """Resolve API key: prompt interactively, or return the provided value."""
    if api_key == "prompt":
        return click.prompt("API key", hide_input=True)
    return api_key


def _make_adapter(name: str, documents: list, api_key: str | None = None):
    """Instantiate an adapter by name."""
    if name == "passthrough":
        from mhd_pos_benchmark.adapters.gold_passthrough import GoldPassthroughAdapter

        return GoldPassthroughAdapter()
    elif name == "majority":
        from mhd_pos_benchmark.adapters.majority_class import MajorityClassAdapter

        adapter = MajorityClassAdapter(documents)
        console.print(f"Majority tag: [bold]{adapter.majority_tag}[/bold]")
        return adapter
    elif name == "gemini":
        from mhd_pos_benchmark.adapters.gemini import GeminiAdapter

        return GeminiAdapter(api_key=api_key)
    elif name == "claude-cli":
        from mhd_pos_benchmark.adapters.claude_cli import ClaudeCliAdapter

        return ClaudeCliAdapter()
    else:
        raise click.UsageError(f"Unknown adapter: {name}")


@click.group()
@click.version_option(package_name="mhd-pos-benchmark")
def cli() -> None:
    """MHD POS Tagging Benchmark — evaluate POS taggers against ReM ground truth."""


@cli.command()
@click.argument("corpus_dir", type=click.Path(exists=True, path_type=Path))
@click.option("--stats", is_flag=True, help="Show corpus statistics")
def parse(corpus_dir: Path, stats: bool) -> None:
    """Parse ReM CORA-XML files and optionally show statistics."""
    from mhd_pos_benchmark.data.rem_parser import parse_corpus

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
        if corpus_dir is None:
            raise click.UsageError("--validate requires --corpus-dir")

        from mhd_pos_benchmark.data.rem_parser import parse_corpus

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
@click.argument("corpus_dir", type=click.Path(exists=True, path_type=Path))
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
def evaluate(
    corpus_dir: Path,
    adapter: str,
    subset: int | None,
    output: Path | None,
    api_key: str | None,
    verbose: bool,
    continue_on_error: bool,
) -> None:
    """Run evaluation pipeline on the corpus."""
    from rich.progress import Progress

    from mhd_pos_benchmark.evaluation.comparator import align_corpus
    from mhd_pos_benchmark.evaluation.metrics import compute_metrics
    from mhd_pos_benchmark.evaluation.report import print_report, save_json

    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    api_key = _resolve_api_key(api_key)
    documents = _parse_and_map(corpus_dir, subset)
    model = _make_adapter(adapter, documents, api_key=api_key)

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
@click.argument("corpus_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--adapters",
    type=str,
    required=True,
    help="Comma-separated adapter names to compare (e.g. 'majority,gemini')",
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
def compare(
    corpus_dir: Path,
    adapters: str,
    subset: int | None,
    output: Path | None,
    api_key: str | None,
    verbose: bool,
    continue_on_error: bool,
) -> None:
    """Compare multiple adapters side-by-side."""
    import json

    from rich.progress import Progress

    from mhd_pos_benchmark.evaluation.comparator import align_corpus
    from mhd_pos_benchmark.evaluation.metrics import EvaluationResult, compute_metrics
    from mhd_pos_benchmark.evaluation.report import print_report

    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    adapter_names = [a.strip() for a in adapters.split(",")]
    api_key = _resolve_api_key(api_key)
    documents = _parse_and_map(corpus_dir, subset)

    results: list[EvaluationResult] = []
    for name in adapter_names:
        model = _make_adapter(name, documents, api_key=api_key)
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
