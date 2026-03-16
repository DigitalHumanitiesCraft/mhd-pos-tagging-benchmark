"""CLI entry point for mhd-bench."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()


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

        # POS tag distribution
        pos_counts: dict[str, int] = {}
        for doc in documents:
            for token in doc.tokens:
                pos_counts[token.pos_hits] = pos_counts.get(token.pos_hits, 0) + 1

        table.add_row("Unique HiTS tags", str(len(pos_counts)))
        console.print(table)

        # Top tags
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
    """Show or validate the HiTS → MHDBDB tagset mapping."""
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
        # Show mapping table
        table = Table(title="HiTS → MHDBDB Mapping")
        table.add_column("HiTS", style="bold")
        table.add_column("MHDBDB")
        for hits, mhdbdb in sorted(mapper.mappings.items()):
            table.add_row(hits, str(mhdbdb) if mhdbdb else "[dim]excluded[/dim]")
        console.print(table)


@cli.command()
@click.argument("corpus_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--adapter",
    type=click.Choice(["passthrough"]),
    default="passthrough",
    help="Model adapter to use",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Save JSON results to this path",
)
def evaluate(corpus_dir: Path, adapter: str, output: Path | None) -> None:
    """Run evaluation pipeline on the corpus."""
    from mhd_pos_benchmark.adapters.gold_passthrough import GoldPassthroughAdapter
    from mhd_pos_benchmark.data.rem_parser import parse_corpus
    from mhd_pos_benchmark.evaluation.comparator import align_corpus
    from mhd_pos_benchmark.evaluation.metrics import compute_metrics
    from mhd_pos_benchmark.evaluation.report import print_report, save_json
    from mhd_pos_benchmark.mapping.tagset_mapper import TagsetMapper

    # Parse
    console.print(f"Parsing corpus from {corpus_dir}...")
    documents = parse_corpus(corpus_dir)
    console.print(f"Parsed {len(documents)} documents")

    # Map
    mapper = TagsetMapper()
    for doc in documents:
        mapper.map_document(doc)

    # Select adapter
    if adapter == "passthrough":
        model = GoldPassthroughAdapter()
    else:
        raise click.UsageError(f"Unknown adapter: {adapter}")

    # Evaluate
    console.print(f"Running evaluation with adapter: {model.name}...")
    alignments = align_corpus(documents, model)
    result = compute_metrics(alignments, model.name)

    # Report
    print_report(result, console)

    if output:
        save_json(result, output)
        console.print(f"\nResults saved to {output}")
