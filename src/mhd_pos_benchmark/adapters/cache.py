"""Result caching — JSONL per document+adapter+version.

Stores one JSON line per document so expensive LLM calls aren't repeated.
Cache key: (adapter_name, document_id). Cache dir: results/<adapter_name>/
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ResultCache:
    """File-based cache for adapter predictions."""

    def __init__(
        self,
        adapter_name: str,
        cache_dir: Path | None = None,
        config_hash: str | None = None,
    ) -> None:
        self._adapter_name = adapter_name
        self._config_hash = config_hash
        self._cache_dir = (cache_dir or Path("results")) / adapter_name
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_file = self._cache_dir / "predictions.jsonl"
        self._cache: dict[str, list[str]] = self._load()

    def _load(self) -> dict[str, list[str]]:
        cache: dict[str, list[str]] = {}
        if self._cache_file.exists():
            for lineno, line in enumerate(
                self._cache_file.read_text(encoding="utf-8").splitlines(), 1
            ):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(
                        "Skipping corrupt cache line %d in %s",
                        lineno, self._cache_file,
                    )
                    continue
                # Skip entries from different config (chunk_size, prompt, etc.)
                if (
                    self._config_hash
                    and entry.get("config_hash")
                    and entry["config_hash"] != self._config_hash
                ):
                    continue
                cache[entry["document_id"]] = entry["predictions"]
        return cache

    def get(self, document_id: str, expected_count: int | None = None) -> list[str] | None:
        cached = self._cache.get(document_id)
        if cached is not None and expected_count is not None:
            if len(cached) != expected_count:
                logger.warning(
                    "Cache length mismatch for %s: cached %d, expected %d — ignoring",
                    document_id, len(cached), expected_count,
                )
                return None
        return cached

    def put(self, document_id: str, predictions: list[str]) -> None:
        already_cached = document_id in self._cache
        self._cache[document_id] = predictions
        if already_cached:
            # Rewrite entire file to avoid duplicate entries
            self._flush()
        else:
            entry = {"document_id": document_id, "predictions": predictions}
            if self._config_hash:
                entry["config_hash"] = self._config_hash
            line = json.dumps(entry, ensure_ascii=False)
            with open(self._cache_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def _flush(self) -> None:
        """Rewrite the cache file from the in-memory dict (compaction)."""
        with open(self._cache_file, "w", encoding="utf-8") as f:
            for doc_id, preds in self._cache.items():
                entry = {"document_id": doc_id, "predictions": preds}
                if self._config_hash:
                    entry["config_hash"] = self._config_hash
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def has(self, document_id: str) -> bool:
        return document_id in self._cache

    @property
    def size(self) -> int:
        return len(self._cache)

    @staticmethod
    def make_config_hash(chunk_size: int, prompt_text: str) -> str:
        """Create a hash from configuration that affects results."""
        data = f"chunk_size={chunk_size}\nprompt={prompt_text}"
        return hashlib.sha256(data.encode()).hexdigest()[:12]
