"""Report generation — console tables and JSON output."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from mhd_pos_benchmark.evaluation.metrics import EvaluationResult


def print_report(result: EvaluationResult, console: Console | None = None) -> None:
    """Print a rich console report of evaluation results."""
    if console is None:
        console = Console()

    console.print(f"\n[bold]Evaluation Report: {result.adapter_name}[/bold]\n")

    # Summary
    summary = Table(title="Summary", show_header=False)
    summary.add_column("Metric", style="bold")
    summary.add_column("Value", justify="right")
    summary.add_row("Documents", str(result.documents_evaluated))
    summary.add_row("Total tokens", str(result.total_tokens))
    summary.add_row("Evaluated tokens", str(result.evaluated_tokens))
    summary.add_row("Excluded tokens", f"{result.excluded_tokens} ({result.exclusion_rate:.1%})")
    summary.add_row("Accuracy", f"{result.accuracy:.4f}")
    summary.add_row("Macro-F1", f"{result.macro_f1:.4f}")
    summary.add_row("Micro-F1", f"{result.micro_f1:.4f}")
    console.print(summary)

    # Per-tag table
    tag_table = Table(title="\nPer-Tag Metrics")
    tag_table.add_column("Tag", style="bold")
    tag_table.add_column("Precision", justify="right")
    tag_table.add_column("Recall", justify="right")
    tag_table.add_column("F1", justify="right")
    tag_table.add_column("Support", justify="right")

    for tm in sorted(result.per_tag, key=lambda t: -t.support):
        tag_table.add_row(
            tm.tag,
            f"{tm.precision:.4f}",
            f"{tm.recall:.4f}",
            f"{tm.f1:.4f}",
            str(tm.support),
        )

    console.print(tag_table)


def save_json(result: EvaluationResult, path: Path) -> None:
    """Save evaluation results as JSON."""
    data = {
        "adapter": result.adapter_name,
        "summary": {
            "accuracy": result.accuracy,
            "macro_f1": result.macro_f1,
            "micro_f1": result.micro_f1,
            "total_tokens": result.total_tokens,
            "evaluated_tokens": result.evaluated_tokens,
            "excluded_tokens": result.excluded_tokens,
            "exclusion_rate": result.exclusion_rate,
            "documents_evaluated": result.documents_evaluated,
        },
        "per_tag": [
            {
                "tag": tm.tag,
                "precision": tm.precision,
                "recall": tm.recall,
                "f1": tm.f1,
                "support": tm.support,
            }
            for tm in result.per_tag
        ],
        "confusion_matrix": {
            "labels": result.confusion_labels,
            "matrix": result.confusion,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
