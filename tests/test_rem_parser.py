"""Tests for the CORA-XML parser."""

from mhd_pos_benchmark.data.rem_parser import parse_document


def test_parse_simple_tokens(sample_cora_path):
    doc = parse_document(sample_cora_path)
    assert doc.id == "T001"
    assert doc.title == "Test Document"
    assert doc.genre == "V"


def test_token_count(sample_cora_path):
    """8 tok_anno elements total (including 2 from multi-mod token t6)."""
    doc = parse_document(sample_cora_path)
    # t1(NA) + t2(VVFIN) + t3(APPR) + t4(DDART) + t5(NA) + t6_m1(APPR) + t6_m2(DDART) + t7($.) + t8(FM) = 9
    assert len(doc.tokens) == 9


def test_multi_mod_token(sample_cora_path):
    """Multi-mod token 'inder' should produce two tokens."""
    doc = parse_document(sample_cora_path)
    # Find tokens from the multi-mod element
    multi_tokens = [t for t in doc.tokens if t.id.startswith("t6")]
    assert len(multi_tokens) == 2
    assert multi_tokens[0].form_modernized == "in"
    assert multi_tokens[0].pos_hits == "APPR"
    assert multi_tokens[1].form_modernized == "der"
    assert multi_tokens[1].pos_hits == "DDART"


def test_pos_tags_extracted(sample_cora_path):
    doc = parse_document(sample_cora_path)
    tags = [t.pos_hits for t in doc.tokens]
    assert "NA" in tags
    assert "VVFIN" in tags
    assert "APPR" in tags
    assert "DDART" in tags
    assert "$_" in tags
    assert "FM" in tags


def test_lemma_extracted(sample_cora_path):
    doc = parse_document(sample_cora_path)
    # First token: ritter → lemma "rîter"
    assert doc.tokens[0].lemma == "rîter"


def test_metadata_extracted(sample_cora_path):
    doc = parse_document(sample_cora_path)
    assert doc.metadata["genre"] == "V"
    assert doc.metadata["title"] == "Test Document"
