"""Gold passthrough adapter — returns mapped ground truth tags.

Used to validate the pipeline: should produce 100% accuracy.
"""

from __future__ import annotations

from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.data.corpus import Document


class GoldPassthroughAdapter(ModelAdapter):
    """Returns the mapped MHDBDB ground truth tags as predictions."""

    @property
    def name(self) -> str:
        return "gold-passthrough"

    def predict(self, document: Document) -> list[str]:
        # mappable_tokens guarantees pos_mhdbdb is not None
        return [t.pos_mhdbdb for t in document.mappable_tokens]  # type: ignore[misc]
