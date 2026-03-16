"""Abstract base class for model adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from mhd_pos_benchmark.data.corpus import Document


class ModelAdapter(ABC):
    """Interface for POS tagging models.

    Each adapter receives a Document (with tokens and their forms) and returns
    a list of MHDBDB POS tag predictions, one per mappable token.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable adapter name."""

    @abstractmethod
    def predict(self, document: Document) -> list[str]:
        """Predict MHDBDB POS tags for all mappable tokens in a document.

        Must return exactly len(document.mappable_tokens) predictions.
        """
