"""Tests for the comparator — aligning predictions to ground truth."""

from __future__ import annotations

import pytest

from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.data.corpus import Document, Token
from mhd_pos_benchmark.evaluation.comparator import align_corpus, align_document


def _make_doc(n_mappable: int = 3, n_excluded: int = 1, doc_id: str = "test") -> Document:
    tokens = [
        Token(id=f"t{i}", form_diplomatic=f"w{i}", form_modernized=f"w{i}",
              pos_hits="NA", pos_mhdbdb="NOM")
        for i in range(n_mappable)
    ]
    tokens += [
        Token(id=f"x{i}", form_diplomatic=".", form_modernized=".",
              pos_hits="$_", pos_mhdbdb=None)
        for i in range(n_excluded)
    ]
    return Document(id=doc_id, tokens=tokens)


class FakeAdapter(ModelAdapter):
    def __init__(self, predictions: list[str]):
        self._predictions = predictions

    @property
    def name(self) -> str:
        return "fake"

    def predict(self, document: Document) -> list[str]:
        return self._predictions


def test_align_document_perfect():
    doc = _make_doc(3, 1)
    adapter = FakeAdapter(["NOM", "NOM", "NOM"])
    result = align_document(doc, adapter)

    assert result.document_id == "test"
    assert result.evaluated_tokens == 3
    assert result.total_tokens == 4
    assert result.excluded_tokens == 1
    assert all(p.gold == p.predicted == "NOM" for p in result.pairs)


def test_align_document_wrong_predictions():
    doc = _make_doc(3)
    adapter = FakeAdapter(["NOM", "VRB", "NOM"])
    result = align_document(doc, adapter)

    assert result.pairs[1].gold == "NOM"
    assert result.pairs[1].predicted == "VRB"


def test_align_document_length_mismatch():
    doc = _make_doc(3)
    adapter = FakeAdapter(["NOM", "NOM"])  # too few
    with pytest.raises(ValueError, match="2 predictions.*3 mappable"):
        align_document(doc, adapter)


def test_align_document_zero_mappable():
    """Document with only excluded tokens should return empty result, not crash."""
    doc = _make_doc(n_mappable=0, n_excluded=5)
    adapter = FakeAdapter([])
    result = align_document(doc, adapter)

    assert result.evaluated_tokens == 0
    assert result.total_tokens == 5
    assert result.excluded_tokens == 5
    assert result.pairs == []


def test_align_corpus_multiple_docs():
    docs = [_make_doc(2, doc_id="d1"), _make_doc(2, doc_id="d2")]
    adapter = FakeAdapter(["NOM", "NOM"])
    results = align_corpus(docs, adapter)

    assert len(results) == 2
    assert results[0].document_id == "d1"
    assert results[1].document_id == "d2"


def test_align_corpus_continue_on_error():
    docs = [_make_doc(2, doc_id="d1"), _make_doc(3, doc_id="d2")]
    # Adapter returns 2 tags — works for d1, fails for d2 (needs 3)
    adapter = FakeAdapter(["NOM", "NOM"])
    results = align_corpus(docs, adapter, continue_on_error=True)

    assert len(results) == 1
    assert results[0].document_id == "d1"


def test_align_corpus_fail_fast():
    docs = [_make_doc(2, doc_id="d1"), _make_doc(3, doc_id="d2")]
    adapter = FakeAdapter(["NOM", "NOM"])
    with pytest.raises(ValueError):
        align_corpus(docs, adapter, continue_on_error=False)


def test_align_corpus_progress_callback():
    docs = [_make_doc(2, doc_id="d1"), _make_doc(2, doc_id="d2")]
    adapter = FakeAdapter(["NOM", "NOM"])
    calls = []
    align_corpus(docs, adapter, progress_callback=lambda: calls.append(1))

    assert len(calls) == 2


def test_aligned_pair_fields():
    doc = _make_doc(1)
    adapter = FakeAdapter(["VRB"])
    result = align_document(doc, adapter)

    pair = result.pairs[0]
    assert pair.token_id == "t0"
    assert pair.form == "w0"
    assert pair.gold == "NOM"
    assert pair.predicted == "VRB"
