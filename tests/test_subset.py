"""Tests for subset selection."""

from __future__ import annotations

import pytest

from mhd_pos_benchmark.data.corpus import Document, Token
from mhd_pos_benchmark.data.subset import (
    describe_subset,
    parse_document_ids,
    select_by_ids,
    select_subset,
)


def _make_doc(doc_id: str, genre: str | None, n_tokens: int = 10) -> Document:
    tokens = [
        Token(id=f"{doc_id}_t{i}", form_diplomatic=f"w{i}", form_modernized=f"w{i}",
              pos_hits="NA", pos_mhdbdb="NOM")
        for i in range(n_tokens)
    ]
    return Document(id=doc_id, genre=genre, tokens=tokens)


def test_basic_subset():
    docs = [_make_doc(f"d{i}", "V", 10) for i in range(20)]
    result = select_subset(docs, n=5)
    assert len(result) <= 5


def test_deterministic_with_seed():
    docs = [_make_doc(f"d{i}", "V", 10 + i) for i in range(20)]
    r1 = select_subset(docs, n=5, seed=42)
    r2 = select_subset(docs, n=5, seed=42)
    assert [d.id for d in r1] == [d.id for d in r2]


def test_different_seed_different_result():
    docs = [_make_doc(f"d{i}", "V", 10 + i) for i in range(20)]
    r1 = select_subset(docs, n=5, seed=42)
    r2 = select_subset(docs, n=5, seed=99)
    assert [d.id for d in r1] != [d.id for d in r2]


def test_stratified_by_genre():
    docs = (
        [_make_doc(f"v{i}", "V", 10) for i in range(10)]
        + [_make_doc(f"p{i}", "P", 10) for i in range(10)]
    )
    result = select_subset(docs, n=4)
    genres = [d.genre for d in result]
    assert "V" in genres
    assert "P" in genres


def test_n_larger_than_corpus():
    docs = [_make_doc(f"d{i}", "V", 10) for i in range(3)]
    result = select_subset(docs, n=10)
    # Should return what it can, not crash
    assert len(result) <= 10


def test_n_equals_1():
    """Edge case: subset of 1 with multiple genres."""
    docs = (
        [_make_doc(f"v{i}", "V", 10) for i in range(5)]
        + [_make_doc(f"p{i}", "P", 10) for i in range(5)]
    )
    result = select_subset(docs, n=1)
    assert len(result) == 1


def test_n_less_than_genres():
    """n=1 but 4 genres — should not infinite loop."""
    docs = [
        _make_doc("v1", "V", 10),
        _make_doc("p1", "P", 10),
        _make_doc("pv1", "PV", 10),
        _make_doc("u1", None, 10),
    ]
    result = select_subset(docs, n=1)
    assert len(result) == 1


def test_describe_subset():
    docs = [
        _make_doc("d1", "V", 5),
        _make_doc("d2", "P", 3),
    ]
    desc = describe_subset(docs)
    assert "2 documents" in desc
    assert "8 mappable tokens" in desc
    assert "V=" in desc
    assert "P=" in desc


class TestParseDocumentIds:
    def test_comma_separated(self):
        assert parse_document_ids("M033,M174,M040") == ["M033", "M174", "M040"]

    def test_whitespace_and_mixed(self):
        assert parse_document_ids("M033, M174  M040") == ["M033", "M174", "M040"]

    def test_deduplicates_keeping_order(self):
        assert parse_document_ids("M033,M174,M033") == ["M033", "M174"]

    def test_empty(self):
        assert parse_document_ids("  ,, ") == []


class TestSelectByIds:
    def test_returns_documents_in_given_order(self):
        docs = [_make_doc("M001", "V"), _make_doc("M002", "P"), _make_doc("M003", "V")]
        result = select_by_ids(docs, ["M003", "M001"])
        assert [d.id for d in result] == ["M003", "M001"]

    def test_unknown_id_raises(self):
        """Silently dropping an ID would change what a published number covers."""
        docs = [_make_doc("M001", "V")]
        with pytest.raises(ValueError, match="not in corpus"):
            select_by_ids(docs, ["M001", "M999"])

    def test_error_lists_every_missing_id(self):
        docs = [_make_doc("M001", "V")]
        with pytest.raises(ValueError, match="2 document ID"):
            select_by_ids(docs, ["X1", "X2"])

    def test_error_suggests_near_misses(self):
        docs = [_make_doc("M033", "V"), _make_doc("M034", "V")]
        with pytest.raises(ValueError, match="did you mean"):
            select_by_ids(docs, ["M035"])
