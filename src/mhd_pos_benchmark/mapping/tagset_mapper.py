"""HiTS → MHDBDB tagset mapping."""

from __future__ import annotations

from pathlib import Path

import yaml

from mhd_pos_benchmark.data.corpus import Document, Token

_YAML_PATH = Path(__file__).parent / "hits_to_mhdbdb.yaml"


class TagsetMapper:
    """Maps HiTS POS tags to MHDBDB POS tags using the YAML definition."""

    def __init__(self, yaml_path: Path = _YAML_PATH) -> None:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        self._mappings: dict[str, str | None] = {}
        for hits_tag, mhdbdb_tag in data["mappings"].items():
            self._mappings[str(hits_tag)] = mhdbdb_tag

    @property
    def mappings(self) -> dict[str, str | None]:
        return dict(self._mappings)

    @property
    def mhdbdb_tags(self) -> set[str]:
        """All unique MHDBDB tags in the mapping (excluding None)."""
        return {v for v in self._mappings.values() if v is not None}

    def map_tag(self, hits_tag: str) -> str | None:
        """Map a single HiTS tag to MHDBDB. Returns None if unmappable, raises if unknown."""
        if hits_tag in self._mappings:
            return self._mappings[hits_tag]
        raise KeyError(f"Unknown HiTS tag: {hits_tag!r}")

    def map_token(self, token: Token) -> Token:
        """Set pos_mhdbdb on a token based on its pos_hits tag."""
        try:
            token.pos_mhdbdb = self.map_tag(token.pos_hits)
        except KeyError:
            token.pos_mhdbdb = None
        return token

    def map_document(self, doc: Document) -> Document:
        """Map all tokens in a document."""
        for token in doc.tokens:
            self.map_token(token)
        return doc

    def find_unmapped(self, documents: list[Document]) -> dict[str, int]:
        """Find HiTS tags in data that are not in the mapping. Returns {tag: count}."""
        unmapped: dict[str, int] = {}
        for doc in documents:
            for token in doc.tokens:
                if token.pos_hits not in self._mappings:
                    unmapped[token.pos_hits] = unmapped.get(token.pos_hits, 0) + 1
        return dict(sorted(unmapped.items(), key=lambda x: -x[1]))
