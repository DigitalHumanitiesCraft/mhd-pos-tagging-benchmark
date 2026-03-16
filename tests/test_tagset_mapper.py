"""Tests for the tagset mapper."""

import pytest

from mhd_pos_benchmark.data.corpus import Token
from mhd_pos_benchmark.mapping.tagset_mapper import TagsetMapper


@pytest.fixture
def mapper():
    return TagsetMapper()


def test_basic_mappings(mapper):
    assert mapper.map_tag("NA") == "NOM"
    assert mapper.map_tag("NE") == "NAM"
    assert mapper.map_tag("VVFIN") == "VRB"
    assert mapper.map_tag("DDART") == "DET"
    assert mapper.map_tag("APPR") == "PRP"
    assert mapper.map_tag("KON") == "CCNJ"
    assert mapper.map_tag("KOUS") == "SCNJ"
    assert mapper.map_tag("CARDA") == "NUM"
    assert mapper.map_tag("ITJ") == "INJ"
    assert mapper.map_tag("PTKNEG") == "NEG"


def test_verb_categories(mapper):
    assert mapper.map_tag("VVFIN") == "VRB"
    assert mapper.map_tag("VAFIN") == "VEX"
    assert mapper.map_tag("VMFIN") == "VEM"


def test_suffix_system(mapper):
    """A=DET, S=PRO, D=ADV, N=PRO for demonstratives."""
    assert mapper.map_tag("DDA") == "DET"
    assert mapper.map_tag("DDS") == "PRO"
    assert mapper.map_tag("DDD") == "ADV"
    assert mapper.map_tag("DDN") == "PRO"


def test_suffix_system_indefinite(mapper):
    assert mapper.map_tag("DIA") == "DET"
    assert mapper.map_tag("DIS") == "PRO"
    assert mapper.map_tag("DID") == "ADV"
    assert mapper.map_tag("DIN") == "PRO"


def test_possessive_mappings(mapper):
    assert mapper.map_tag("DPOSA") == "POS"
    assert mapper.map_tag("DPOSS") == "POS"
    assert mapper.map_tag("DPOSN") == "POS"
    assert mapper.map_tag("DPOSD") == "POS"


def test_relative_and_generalized(mapper):
    assert mapper.map_tag("DRELS") == "PRO"
    assert mapper.map_tag("DGA") == "DET"
    assert mapper.map_tag("DGS") == "PRO"


def test_pronominal_adverbs(mapper):
    assert mapper.map_tag("PAVD") == "ADV"
    assert mapper.map_tag("PAVAP") == "ADV"
    assert mapper.map_tag("PAVW") == "ADV"
    assert mapper.map_tag("PAVG") == "ADV"


def test_ptkant(mapper):
    assert mapper.map_tag("PTKANT") == "INJ"


def test_unmappable_tags(mapper):
    assert mapper.map_tag("FM") is None
    assert mapper.map_tag("$_") is None
    assert mapper.map_tag("--") is None
    assert mapper.map_tag("KO*") is None


def test_unknown_tag_raises(mapper):
    with pytest.raises(KeyError, match="Unknown HiTS tag"):
        mapper.map_tag("NONEXISTENT")


def test_map_token(mapper):
    token = Token(id="t1", form_diplomatic="ritter", form_modernized="ritter", pos_hits="NA")
    mapper.map_token(token)
    assert token.pos_mhdbdb == "NOM"


def test_map_token_unmappable(mapper):
    token = Token(id="t1", form_diplomatic=".", form_modernized=".", pos_hits="$_")
    mapper.map_token(token)
    assert token.pos_mhdbdb is None
    assert not token.is_mappable


def test_all_16_mapped_mhdbdb_tags_present(mapper):
    """16 of 19 MHDBDB tags have direct mappings. Missing: IPA, CNJ, DIG (no HiTS source)."""
    expected = {"NOM", "NAM", "ADJ", "ADV", "DET", "POS", "PRO", "PRP", "NEG",
                "NUM", "SCNJ", "CCNJ", "VRB", "VEX", "VEM", "INJ"}
    actual = mapper.mhdbdb_tags
    assert expected.issubset(actual), f"Missing: {expected - actual}"
    # These 3 have no HiTS source — expected absent
    assert "IPA" not in actual
    assert "CNJ" not in actual
    assert "DIG" not in actual
