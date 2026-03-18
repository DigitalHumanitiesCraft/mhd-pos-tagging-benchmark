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
    is_multimod: bool = False

    @property
    def form_for_tagging(self) -> str:
        """The form to send to POS taggers.

        For regular tokens: the diplomatic (written) form.
        For multi-mod sub-tokens: the modernized (analyzed) form,
        since the diplomatic form is the unsplit combined form (e.g., 'inder')
        which would be misleading if sent once per sub-token.
        """
        return self.form_modernized if self.is_multimod else self.form_diplomatic

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
