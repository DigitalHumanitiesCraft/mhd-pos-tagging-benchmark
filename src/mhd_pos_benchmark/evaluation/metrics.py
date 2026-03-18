"""Compute evaluation metrics from alignment results."""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

from mhd_pos_benchmark.evaluation.comparator import AlignmentResult


@dataclass
class TagMetrics:
    """Per-tag precision, recall, F1."""

    tag: str
    precision: float
    recall: float
    f1: float
    support: int


@dataclass
class EvaluationResult:
    """Full evaluation metrics for a benchmark run."""

    adapter_name: str
    accuracy: float
    macro_f1: float
    micro_f1: float
    per_tag: list[TagMetrics]
    confusion: list[list[int]]
    confusion_labels: list[str]
    total_tokens: int
    evaluated_tokens: int
    excluded_tokens: int
    documents_evaluated: int

    @property
    def exclusion_rate(self) -> float:
        return self.excluded_tokens / self.total_tokens if self.total_tokens else 0.0


def compute_metrics(
    results: list[AlignmentResult], adapter_name: str
) -> EvaluationResult:
    """Compute all metrics from alignment results."""
    gold_tags: list[str] = []
    pred_tags: list[str] = []
    total_tokens = 0
    excluded_tokens = 0

    for result in results:
        total_tokens += result.total_tokens
        excluded_tokens += result.excluded_tokens
        for pair in result.pairs:
            gold_tags.append(pair.gold)
            pred_tags.append(pair.predicted)

    if not gold_tags:
        raise ValueError("No evaluated tokens — cannot compute metrics")

    # Sorted label set for consistent ordering
    labels = sorted(set(gold_tags) | set(pred_tags))

    acc = accuracy_score(gold_tags, pred_tags)
    macro_f1 = f1_score(gold_tags, pred_tags, labels=labels, average="macro", zero_division=0)
    micro_f1 = f1_score(gold_tags, pred_tags, labels=labels, average="micro", zero_division=0)

    prec, rec, f1, support = precision_recall_fscore_support(
        gold_tags, pred_tags, labels=labels, zero_division=0
    )

    per_tag = [
        TagMetrics(tag=label, precision=p, recall=r, f1=f, support=int(s))
        for label, p, r, f, s in zip(labels, prec, rec, f1, support)
    ]

    cm = confusion_matrix(gold_tags, pred_tags, labels=labels)

    return EvaluationResult(
        adapter_name=adapter_name,
        accuracy=acc,
        macro_f1=macro_f1,
        micro_f1=micro_f1,
        per_tag=per_tag,
        confusion=cm.tolist(),
        confusion_labels=labels,
        total_tokens=total_tokens,
        evaluated_tokens=len(gold_tags),
        excluded_tokens=excluded_tokens,
        documents_evaluated=sum(1 for r in results if r.pairs),
    )
