"""Tests for shared prompt template and response parsing.

These tests cover parse_tag_response() which is shared across all LLM adapters.
Adapter-specific tests are in test_generic_cli.py and test_generic_api.py.
"""

from __future__ import annotations

import json

import pytest

from mhd_pos_benchmark.adapters.prompt_template import parse_tag_response


class TestParseTagResponse:
    def test_valid_json_array(self):
        text = '["NOM", "VRB", "DET"]'
        assert parse_tag_response(text, 3) == ["NOM", "VRB", "DET"]

    def test_strips_markdown_fences(self):
        text = "```json\n[\"NOM\", \"VRB\"]\n```"
        assert parse_tag_response(text, 2) == ["NOM", "VRB"]

    def test_wrong_count_raises(self):
        with pytest.raises(ValueError, match="Expected 3 tags, got 2"):
            parse_tag_response('["NOM", "VRB"]', 3)

    def test_invalid_tag_raises(self):
        with pytest.raises(ValueError, match="invalid tags"):
            parse_tag_response('["NOM", "BOGUS"]', 2)

    def test_not_a_list_raises(self):
        with pytest.raises(ValueError, match="Expected JSON array"):
            parse_tag_response('{"tag": "NOM"}', 1)

    def test_bad_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_tag_response("not json at all", 1)

    def test_trailing_text_after_json(self):
        text = 'Here are the tags: ["NOM", "VRB"] I hope that helps'
        assert parse_tag_response(text, 2) == ["NOM", "VRB"]

    def test_fences_with_trailing_explanation(self):
        text = "```json\n[\"NOM\", \"VRB\"]\n```\nSome explanation"
        assert parse_tag_response(text, 2) == ["NOM", "VRB"]
