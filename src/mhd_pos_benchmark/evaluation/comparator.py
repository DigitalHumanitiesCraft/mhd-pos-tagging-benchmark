"""Align predictions to ground truth for evaluation."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.data.corpus import Document

logger = logging.getLogger(__name__)


@dataclass
class AlignedPair:
    """A single ground-truth / prediction pair."""

    token_id: str
    form: str
    form_diplomatic: str
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

    if not mappable:
        raise ValueError(
            f"Document {document.id}: no mappable tokens — "
            f"was map_document() called?"
        )

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
            form_diplomatic=token.form_diplomatic,
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
    documents: list[Document],
    adapter: ModelAdapter,
    continue_on_error: bool = False,
    progress_callback: Callable[[], None] | None = None,
) -> list[AlignmentResult]:
    """Run adapter on all documents and collect alignment results."""
    results: list[AlignmentResult] = []
    for doc in documents:
        try:
            results.append(align_document(doc, adapter))
        except Exception as e:
            if continue_on_error:
                logger.error("Skipping document %s: %s", doc.id, e)
            else:
                raise
        finally:
            if progress_callback is not None:
                progress_callback()
    return results
