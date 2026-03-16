"""Align predictions to ground truth for evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.data.corpus import Document


@dataclass
class AlignedPair:
    """A single ground-truth / prediction pair."""

    token_id: str
    form: str
    gold: str
    predicted: str


@dataclass
class AlignmentResult:
    """Result of aligning predictions to ground truth for one document."""

    document_id: str
    pairs: list[AlignedPair]
    total_tokens: int
    excluded_tokens: int

    @property
    def evaluated_tokens(self) -> int:
        return len(self.pairs)


def align_document(document: Document, adapter: ModelAdapter) -> AlignmentResult:
    """Run adapter on a document and align predictions with ground truth."""
    mappable = document.mappable_tokens
    predictions = adapter.predict(document)

    if len(predictions) != len(mappable):
        raise ValueError(
            f"Document {document.id}: adapter returned {len(predictions)} predictions "
            f"but document has {len(mappable)} mappable tokens"
        )

    pairs = [
        AlignedPair(
            token_id=token.id,
            form=token.form_modernized,
            gold=token.pos_mhdbdb,
            predicted=pred,
        )
        for token, pred in zip(mappable, predictions)
    ]

    return AlignmentResult(
        document_id=document.id,
        pairs=pairs,
        total_tokens=len(document.tokens),
        excluded_tokens=len(document.excluded_tokens),
    )


def align_corpus(
    documents: list[Document], adapter: ModelAdapter
) -> list[AlignmentResult]:
    """Run adapter on all documents and collect alignment results."""
    return [align_document(doc, adapter) for doc in documents]
