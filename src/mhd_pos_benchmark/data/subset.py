"""Subset selection — pick representative documents for prototyping.

Selects documents across genres and sizes for fast iteration
before running expensive evaluations on the full corpus.

Two selection modes:

- `select_subset(documents, n)` — genre-stratified sample, deterministic for a
  given corpus and n. Good for exploring, but the sample shifts when the corpus
  or the allocation logic changes, which silently detaches earlier cached runs.
- `select_by_ids(documents, ids)` — exactly the documents named. This is what
  published runs should use: the document list becomes part of the method
  description rather than an artefact of the sampling code.
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


def parse_document_ids(raw: str) -> list[str]:
    """Split a comma or whitespace separated document ID list, preserving order."""
    ids = [part.strip() for part in raw.replace(",", " ").split()]
    seen: set[str] = set()
    unique: list[str] = []
    for doc_id in ids:
        if not doc_id or doc_id in seen:
            continue
        seen.add(doc_id)
        unique.append(doc_id)
    return unique


def select_by_ids(documents: list[Document], ids: list[str]) -> list[Document]:
    """Select exactly the documents named, in the order given.

    Raises ValueError listing every unknown ID, with near-miss suggestions.
    Being strict is the point: silently dropping an unknown ID would change
    what a published number covers without saying so.
    """
    by_id = {doc.id: doc for doc in documents}
    missing = [doc_id for doc_id in ids if doc_id not in by_id]

    if missing:
        hints = []
        for doc_id in missing[:3]:
            close = [
                known for known in by_id
                if known.upper().startswith(doc_id.upper()[:2])
            ]
            if close:
                hints.append(f"{doc_id} (did you mean {', '.join(sorted(close)[:3])}?)")
            else:
                hints.append(doc_id)
        raise ValueError(
            f"{len(missing)} document ID(s) not in corpus: {', '.join(hints)}. "
            f"Corpus has {len(by_id)} documents."
        )

    return [by_id[doc_id] for doc_id in ids]


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
