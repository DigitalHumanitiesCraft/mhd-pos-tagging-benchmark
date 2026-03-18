"""Subset selection — pick representative documents for prototyping.

Selects documents across genres and sizes for fast iteration
before running expensive evaluations on the full corpus.
"""

from __future__ import annotations

import logging
import random
from collections import defaultdict

from mhd_pos_benchmark.data.corpus import Document

logger = logging.getLogger(__name__)


def select_subset(
    documents: list[Document],
    n: int = 10,
    seed: int = 42,
) -> list[Document]:
    """Select a representative subset stratified by genre.

    Strategy:
    1. Group documents by genre (V=Vers, P=Prosa, PV=mixed, None=unknown)
    2. Pick proportionally from each genre
    3. Within each genre, pick documents near median size (not outliers)
    """
    rng = random.Random(seed)

    by_genre: dict[str | None, list[Document]] = defaultdict(list)
    for doc in documents:
        by_genre[doc.genre].append(doc)

    # Sort each genre by token count (ascending)
    for genre_docs in by_genre.values():
        genre_docs.sort(key=lambda d: len(d.mappable_tokens))

    selected: list[Document] = []

    # Proportional allocation, at least 1 per genre
    genre_counts: dict[str | None, int] = {}
    for genre, docs in by_genre.items():
        genre_counts[genre] = max(1, round(n * len(docs) / len(documents)))

    # Adjust to hit exactly n
    total_allocated = sum(genre_counts.values())
    while total_allocated > n:
        # Trim one from the largest genre (but never below 1, or 0 as last resort)
        candidates = [g for g in genre_counts if genre_counts[g] > 1]
        if not candidates:
            # All genres are at 1 — must drop some to 0
            candidates = [g for g in genre_counts if genre_counts[g] > 0]
            if not candidates:
                break
        largest = max(candidates, key=lambda g: genre_counts[g])
        genre_counts[largest] -= 1
        total_allocated -= 1

    for genre, count in genre_counts.items():
        docs = by_genre[genre]
        if not docs:
            continue

        # Pick from the middle third (avoid tiny/huge outliers)
        third = max(1, len(docs) // 3)
        middle = docs[third : 2 * third] if len(docs) > 3 else docs
        picks = rng.sample(middle, min(count, len(middle)))
        selected.extend(picks)

    if len(selected) < n:
        logger.warning(
            "Subset returned %d documents instead of requested %d",
            len(selected), n,
        )
    return selected[:n]


def describe_subset(documents: list[Document]) -> str:
    """Return a human-readable summary of a subset."""
    lines = []
    total_tokens = sum(len(d.mappable_tokens) for d in documents)
    genres = defaultdict(int)
    for d in documents:
        genres[d.genre or "unknown"] += 1

    lines.append(f"{len(documents)} documents, {total_tokens} mappable tokens")
    lines.append("Genres: " + ", ".join(f"{g}={c}" for g, c in sorted(genres.items())))
    for d in documents:
        lines.append(f"  {d.id}: {d.genre or '?'}, {len(d.mappable_tokens)} tokens")
    return "\n".join(lines)
