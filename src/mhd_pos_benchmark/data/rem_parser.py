"""Parser for ReM CORA-XML files."""

from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from mhd_pos_benchmark.data.corpus import Document, Token

logger = logging.getLogger(__name__)

# Header fields to extract as metadata
_HEADER_FIELDS = [
    "title", "abbr_ddd", "abbr_mwb", "topic", "text-type", "genre",
    "language-area", "date", "text-author", "annotation_by", "edition",
]


def parse_document(path: Path) -> Document:
    """Parse a single CORA-XML file into a Document."""
    tree = etree.parse(path)
    root = tree.getroot()

    doc_id = root.get("id", path.stem)
    metadata = _extract_metadata(root)

    tokens: list[Token] = []
    for token_el in root.iter("token"):
        tokens.extend(_parse_token(token_el))

    return Document(
        id=doc_id,
        title=metadata.get("title"),
        genre=metadata.get("genre"),
        tokens=tokens,
        metadata=metadata,
    )


def parse_corpus(corpus_dir: Path) -> list[Document]:
    """Parse all CORA-XML files in a directory."""
    xml_files = sorted(corpus_dir.glob("*.xml"))
    if not xml_files:
        raise FileNotFoundError(f"No XML files found in {corpus_dir}")
    return [parse_document(f) for f in xml_files]


def _extract_metadata(root: etree._Element) -> dict[str, str]:
    """Extract metadata from the <header> element."""
    metadata: dict[str, str] = {}
    header = root.find("header")
    if header is None:
        return metadata
    for field_name in _HEADER_FIELDS:
        el = header.find(field_name)
        if el is not None and el.text:
            metadata[field_name] = el.text.strip()
    return metadata


def _parse_token(token_el: etree._Element) -> list[Token]:
    """Parse a <token> element into one or more Tokens.

    Multi-mod tokens (clitics) yield multiple Token objects.
    """
    tokens: list[Token] = []
    skipped = 0

    # Get diplomatic form from tok_dipl (first one for display)
    dipl_el = token_el.find("tok_dipl")
    dipl_utf = dipl_el.get("utf", "") if dipl_el is not None else ""

    # Detect multi-mod (clitic) tokens: >1 tok_anno under one <token>
    anno_elements = token_el.findall("tok_anno")
    is_multimod = len(anno_elements) > 1

    for anno_el in anno_elements:
        pos_el = anno_el.find("pos")
        if pos_el is None:
            skipped += 1
            continue

        pos_tag = pos_el.get("tag", "")
        if not pos_tag:
            skipped += 1
            continue

        anno_id = anno_el.get("id", "")
        mod_utf = anno_el.get("utf", "")

        lemma_el = anno_el.find("lemma")
        lemma = lemma_el.get("tag") if lemma_el is not None else None

        tokens.append(Token(
            id=anno_id,
            form_diplomatic=dipl_utf,
            form_modernized=mod_utf,
            pos_hits=pos_tag,
            lemma=lemma,
            is_multimod=is_multimod,
        ))

    if skipped:
        logger.debug(
            "Skipped %d tok_anno without POS in token %s",
            skipped, token_el.get("id", "?"),
        )
    return tokens
