"""Tests for evaluation metrics."""

from mhd_pos_benchmark.evaluation.comparator import AlignedPair, AlignmentResult
from mhd_pos_benchmark.evaluation.metrics import compute_metrics


def _make_result(pairs, doc_id="test", total=None, excluded=0):
    if total is None:
        total = len(pairs) + excluded
    return AlignmentResult(
        document_id=doc_id,
        pairs=pairs,
        total_tokens=total,
        excluded_tokens=excluded,
    )


def test_perfect_accuracy():
    pairs = [
        AlignedPair("t1", "ritter", "NOM", "NOM"),
        AlignedPair("t2", "reit", "VRB", "VRB"),
        AlignedPair("t3", "in", "PRP", "PRP"),
    ]
    result = compute_metrics([_make_result(pairs)], "test")
    assert result.accuracy == 1.0
    assert result.macro_f1 == 1.0
    assert result.micro_f1 == 1.0


def test_partial_accuracy():
    pairs = [
        AlignedPair("t1", "ritter", "NOM", "NOM"),
        AlignedPair("t2", "reit", "VRB", "ADV"),  # wrong
        AlignedPair("t3", "in", "PRP", "PRP"),
    ]
    result = compute_metrics([_make_result(pairs)], "test")
    assert abs(result.accuracy - 2 / 3) < 1e-6


def test_token_counts():
    pairs = [AlignedPair("t1", "x", "NOM", "NOM")]
    result = compute_metrics([_make_result(pairs, total=10, excluded=9)], "test")
    assert result.total_tokens == 10
    assert result.evaluated_tokens == 1
    assert result.excluded_tokens == 9


def test_confusion_matrix_shape():
    pairs = [
        AlignedPair("t1", "a", "NOM", "NOM"),
        AlignedPair("t2", "b", "VRB", "NOM"),
    ]
    result = compute_metrics([_make_result(pairs)], "test")
    n_labels = len(result.confusion_labels)
    assert len(result.confusion) == n_labels
    assert all(len(row) == n_labels for row in result.confusion)
