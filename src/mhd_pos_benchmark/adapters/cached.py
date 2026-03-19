"""Cached adapter — replays predictions from a previous evaluate run.

Used by `compare --models` to compare results without re-running expensive
LLM calls. Loads predictions from results/<model>/predictions.jsonl.
"""

from __future__ import annotations

import logging
from pathlib import Path

from mhd_pos_benchmark.adapters.base import ModelAdapter
from mhd_pos_benchmark.adapters.cache import ResultCache
from mhd_pos_benchmark.data.corpus import Document

logger = logging.getLogger(__name__)


class CachedAdapter(ModelAdapter):
    """Replays cached predictions from a previous evaluation run.

    Raises ValueError if a document is not found in the cache —
    run `evaluate` first to populate the cache.
    """

    def __init__(self, model_name: str, cache_dir: Path | None = None) -> None:
        self._model_name = model_name
        self._cache_dir = cache_dir or Path("results")
        cache_path = self._cache_dir / model_name
        if not (cache_path / "predictions.jsonl").exists():
            available = self._list_cached_models()
            msg = f"No cached results for '{model_name}'."
            if available:
                msg += f" Available: {', '.join(available)}"
            else:
                msg += " Run 'mhd-bench evaluate' first to generate results."
            raise FileNotFoundError(msg)
        # Load without config_hash filtering — accept all cached entries
        self._cache = ResultCache(model_name, cache_dir)

    @property
    def name(self) -> str:
        return self._model_name

    def predict(self, document: Document) -> list[str]:
        mappable = document.mappable_tokens
        cached = self._cache.get(document.id, expected_count=len(mappable))
        if cached is not None:
            return cached
        raise ValueError(
            f"Document {document.id} not found in cache for '{self._model_name}'. "
            f"Run 'mhd-bench evaluate' with --model {self._model_name} first."
        )

    def _list_cached_models(self) -> list[str]:
        """List model names that have cached predictions."""
        if not self._cache_dir.exists():
            return []
        return sorted(
            d.name for d in self._cache_dir.iterdir()
            if d.is_dir() and (d / "predictions.jsonl").exists()
        )
