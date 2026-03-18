"""Tests for report generation (console + JSON)."""

from __future__ import annotations

import json

from rich.console import Console

from mhd_pos_benchmark.evaluation.comparator import AlignedPair, AlignmentResult
from mhd_pos_benchmark.evaluation.metrics import compute_metrics
from mhd_pos_benchmark.evaluation.report import print_report, save_json


def _make_eval_result():
    """Create a minimal EvaluationResult for testing."""
    pairs = [
        AlignedPair("t1", "ritter", "ritter", "NOM", "NOM"),
        AlignedPair("t2", "reit", "reit", "VRB", "VRB"),
        AlignedPair("t3", "in", "in", "PRP", "ADV"),  # one error
    ]
    alignment = AlignmentResult(
        document_id="test-doc",
        pairs=pairs,
        total_tokens=5,
        excluded_tokens=2,
    )
    return compute_metrics([alignment], "test-adapter")


def test_print_report_runs():
    """print_report should not raise."""
    result = _make_eval_result()
    console = Console(file=None, force_terminal=False)
    print_report(result, console)


def test_print_report_default_console():
    result = _make_eval_result()
    print_report(result)  # should use default console


def test_save_json_creates_file(tmp_path):
    result = _make_eval_result()
    out = tmp_path / "result.json"
    save_json(result, out)
    assert out.exists()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["adapter"] == "test-adapter"
    assert "summary" in data
    assert "per_tag" in data
    assert "confusion_matrix" in data


def test_save_json_schema(tmp_path):
    result = _make_eval_result()
    out = tmp_path / "result.json"
    save_json(result, out)
    data = json.loads(out.read_text(encoding="utf-8"))

    summary = data["summary"]
    assert "accuracy" in summary
    assert "macro_f1" in summary
    assert "micro_f1" in summary
    assert "total_tokens" in summary
    assert "evaluated_tokens" in summary
    assert "excluded_tokens" in summary
    assert "exclusion_rate" in summary
    assert "documents_evaluated" in summary

    # Per-tag entries
    for entry in data["per_tag"]:
        assert "tag" in entry
        assert "precision" in entry
        assert "recall" in entry
        assert "f1" in entry
        assert "support" in entry

    # Confusion matrix
    cm = data["confusion_matrix"]
    assert "labels" in cm
    assert "matrix" in cm
    assert len(cm["matrix"]) == len(cm["labels"])


def test_save_json_creates_parent_dirs(tmp_path):
    result = _make_eval_result()
    out = tmp_path / "sub" / "dir" / "result.json"
    save_json(result, out)
    assert out.exists()
