"""Result caching — JSONL per document+adapter+version.

Stores one JSON line per document so expensive LLM calls aren't repeated.
Cache key: (adapter_name, document_id). Cache dir: results/<adapter_name>/
"""

from __future__ import annotations

import json
from pathlib import Path


class ResultCache:
    """File-based cache for adapter predictions."""

    def __init__(self, adapter_name: str, cache_dir: Path | None = None) -> None:
        self._adapter_name = adapter_name
        self._cache_dir = (cache_dir or Path("results")) / adapter_name
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_file = self._cache_dir / "predictions.jsonl"
        self._cache: dict[str, list[str]] = self._load()

    def _load(self) -> dict[str, list[str]]:
        cache: dict[str, list[str]] = {}
        if self._cache_file.exists():
            for line in self._cache_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    entry = json.loads(line)
                    cache[entry["document_id"]] = entry["predictions"]
        return cache

    def get(self, document_id: str) -> list[str] | None:
        return self._cache.get(document_id)

    def put(self, document_id: str, predictions: list[str]) -> None:
        self._cache[document_id] = predictions
        entry = json.dumps(
            {"document_id": document_id, "predictions": predictions},
            ensure_ascii=False,
        )
        with open(self._cache_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def has(self, document_id: str) -> bool:
        return document_id in self._cache

    @property
    def size(self) -> int:
        return len(self._cache)
