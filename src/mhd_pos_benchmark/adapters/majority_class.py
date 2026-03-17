"""Majority-class baseline adapter — assigns the most frequent tag to every token.

Provides a trivial lower bound: any real model should beat this.
Trains on the corpus itself (cheating baseline), so accuracy represents
the proportion of tokens carrying the most frequent MHDBDB tag.
"""

from __future__ import annotations

from collections import Counter

from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.data.corpus import Document


class MajorityClassAdapter(ModelAdapter):
    """Always predicts the single most frequent MHDBDB tag from the training set."""

    def __init__(self, documents: list[Document]) -> None:
        tag_counts: Counter[str] = Counter()
        for doc in documents:
            for token in doc.mappable_tokens:
                tag_counts[token.pos_mhdbdb] += 1

        if not tag_counts:
            raise ValueError("No mappable tokens in corpus — cannot determine majority class")

        self._majority_tag = tag_counts.most_common(1)[0][0]
        self._tag_counts = tag_counts

    @property
    def name(self) -> str:
        return "majority-class"

    @property
    def majority_tag(self) -> str:
        return self._majority_tag

    def predict(self, document: Document) -> list[str]:
        return [self._majority_tag] * len(document.mappable_tokens)
