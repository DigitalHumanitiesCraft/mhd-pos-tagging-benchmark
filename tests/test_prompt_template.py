"""Tests for prompt building and chunking."""

from __future__ import annotations

from mhd_pos_benchmark.adapters.prompt_template import (
    build_chunked_prompts,
    build_tagging_prompt,
)


def test_build_tagging_prompt_numbers_words():
    prompt = build_tagging_prompt(["ritter", "reit", "in"])
    assert "1. ritter" in prompt
    assert "2. reit" in prompt
    assert "3. in" in prompt
    assert "Tag each word" in prompt


def test_build_tagging_prompt_empty():
    prompt = build_tagging_prompt([])
    assert "Tag each word" in prompt


def test_build_chunked_prompts_single_chunk():
    forms = ["w1", "w2", "w3"]
    chunks = build_chunked_prompts(forms, chunk_size=10)
    assert len(chunks) == 1
    start, end, prompt = chunks[0]
    assert start == 0
    assert end == 3
    assert "w1" in prompt


def test_build_chunked_prompts_multiple():
    forms = [f"w{i}" for i in range(5)]
    chunks = build_chunked_prompts(forms, chunk_size=2)
    assert len(chunks) == 3  # 2+2+1
    assert chunks[0] == (0, 2, build_tagging_prompt(["w0", "w1"]))
    assert chunks[1] == (2, 4, build_tagging_prompt(["w2", "w3"]))
    assert chunks[2] == (4, 5, build_tagging_prompt(["w4"]))


def test_build_chunked_prompts_exact_fit():
    forms = ["w1", "w2", "w3", "w4"]
    chunks = build_chunked_prompts(forms, chunk_size=2)
    assert len(chunks) == 2
    assert chunks[0][0:2] == (0, 2)
    assert chunks[1][0:2] == (2, 4)


def test_build_chunked_prompts_empty():
    chunks = build_chunked_prompts([], chunk_size=100)
    assert chunks == []


def test_chunk_prompts_are_numbered_from_1():
    """Each chunk numbers its words from 1, not from the global offset."""
    forms = [f"w{i}" for i in range(4)]
    chunks = build_chunked_prompts(forms, chunk_size=2)
    # Second chunk should number w2 as "1." not "3."
    assert "1. w2" in chunks[1][2]
    assert "2. w3" in chunks[1][2]
