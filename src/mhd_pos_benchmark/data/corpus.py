"""Data model for the MHD POS benchmark."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Token:
    """A single annotatable unit (one tok_anno element from CORA-XML)."""

    id: str
    form_diplomatic: str
    form_modernized: str
    pos_hits: str
    pos_mhdbdb: str | None = None
    lemma: str | None = None

    @property
    def is_mappable(self) -> bool:
        """Whether this token has a valid MHDBDB mapping (not excluded)."""
        return self.pos_mhdbdb is not None


@dataclass
class Document:
    """A parsed CORA-XML document with its tokens and metadata."""

    id: str
    title: str | None = None
    genre: str | None = None
    tokens: list[Token] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def mappable_tokens(self) -> list[Token]:
        """Tokens that have a valid MHDBDB tag (included in evaluation)."""
        return [t for t in self.tokens if t.is_mappable]

    @property
    def excluded_tokens(self) -> list[Token]:
        """Tokens excluded from evaluation (FM, punctuation, etc.)."""
        return [t for t in self.tokens if not t.is_mappable]
