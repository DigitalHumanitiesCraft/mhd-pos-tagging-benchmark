"""Tests for the Gemini API adapter.

Mocks the google-genai SDK so no real API key or package install is needed.
"""

from __future__ import annotations

import json
import sys
import types
import uuid

import pytest

from mhd_pos_benchmark.data.corpus import Document, Token


def _make_document(n_tokens: int = 5, doc_id: str | None = None) -> Document:
    tokens = [
        Token(
            id=f"t{i}",
            form_diplomatic=f"wort{i}",
            form_modernized=f"wort{i}",
            pos_hits="NA",
            pos_mhdbdb="NOM",
        )
        for i in range(n_tokens)
    ]
    return Document(id=doc_id or f"test-{uuid.uuid4().hex[:8]}", title="Test", tokens=tokens)


class FakeResponse:
    def __init__(self, text: str | None):
        self.text = text


class FakeModels:
    def __init__(self, responses: list[FakeResponse]):
        self._responses = responses
        self._call_count = 0

    def generate_content(self, **kwargs):
        idx = self._call_count
        self._call_count += 1
        return self._responses[idx]


class FakeClient:
    def __init__(self, api_key: str = "test"):
        self.models = None  # set later by _make_adapter


class FakeGenerateContentConfig:
    def __init__(self, **kwargs):
        pass


@pytest.fixture(autouse=True)
def mock_google_genai(monkeypatch):
    """Install fake google.genai module so GeminiAdapter can be imported without the real SDK."""
    # Build fake module hierarchy: google -> google.genai -> google.genai.types
    google_mod = types.ModuleType("google")
    genai_mod = types.ModuleType("google.genai")
    types_mod = types.ModuleType("google.genai.types")

    genai_mod.Client = FakeClient
    types_mod.GenerateContentConfig = FakeGenerateContentConfig

    google_mod.genai = genai_mod
    genai_mod.types = types_mod

    monkeypatch.setitem(sys.modules, "google", google_mod)
    monkeypatch.setitem(sys.modules, "google.genai", genai_mod)
    monkeypatch.setitem(sys.modules, "google.genai.types", types_mod)


def _make_adapter(tmp_path, responses, **kwargs):
    """Create a GeminiAdapter with mocked client."""
    from mhd_pos_benchmark.adapters.gemini import GeminiAdapter

    adapter = GeminiAdapter(api_key="test-key", cache_dir=tmp_path, **kwargs)
    adapter._client.models = FakeModels(responses)
    return adapter


def test_name(tmp_path):
    from mhd_pos_benchmark.adapters.gemini import GeminiAdapter

    adapter = GeminiAdapter(api_key="test-key", cache_dir=tmp_path)
    # Default model is gemini-3.1-pro — no double prefix
    assert adapter.name == "gemini-3.1-pro"
    assert "gemini-gemini" not in adapter.name


def test_predict_basic(tmp_path):
    tags = ["NOM", "NOM", "NOM", "NOM", "NOM"]
    responses = [FakeResponse(json.dumps(tags))]
    adapter = _make_adapter(tmp_path, responses)
    doc = _make_document(5)
    result = adapter.predict(doc)
    assert result == tags


def test_caching(tmp_path):
    tags = ["NOM", "NOM", "NOM", "NOM", "NOM"]
    responses = [FakeResponse(json.dumps(tags))]
    adapter = _make_adapter(tmp_path, responses)
    doc = _make_document(5)

    result1 = adapter.predict(doc)
    result2 = adapter.predict(doc)  # should use cache, not call API again

    assert result1 == result2 == tags
    # Only one API call was made (FakeModels would IndexError on second call)


def test_chunking(tmp_path):
    responses = [
        FakeResponse(json.dumps(["NOM", "NOM", "NOM"])),
        FakeResponse(json.dumps(["NOM", "NOM"])),
    ]
    adapter = _make_adapter(tmp_path, responses, chunk_size=3)
    doc = _make_document(5)
    result = adapter.predict(doc)

    assert result == ["NOM"] * 5


def test_no_api_key_raises():
    import os

    env_backup = os.environ.pop("GEMINI_API_KEY", None)
    try:
        from mhd_pos_benchmark.adapters.gemini import GeminiAdapter

        with pytest.raises(OSError, match="No API key"):
            GeminiAdapter()
    finally:
        if env_backup is not None:
            os.environ["GEMINI_API_KEY"] = env_backup


def test_safety_filter_retries(tmp_path, monkeypatch):
    """Blocked response (text=None) should trigger retry."""
    monkeypatch.setattr("mhd_pos_benchmark.adapters.gemini.time.sleep", lambda _: None)
    responses = [
        FakeResponse(None),  # blocked
        FakeResponse(json.dumps(["NOM"])),
    ]
    adapter = _make_adapter(tmp_path, responses, max_retries=2)
    doc = _make_document(1)
    result = adapter.predict(doc)
    assert result == ["NOM"]


def test_bad_json_retries(tmp_path, monkeypatch):
    monkeypatch.setattr("mhd_pos_benchmark.adapters.gemini.time.sleep", lambda _: None)
    responses = [
        FakeResponse("not valid json"),
        FakeResponse(json.dumps(["NOM"])),
    ]
    adapter = _make_adapter(tmp_path, responses, max_retries=2)
    doc = _make_document(1)
    result = adapter.predict(doc)
    assert result == ["NOM"]


def test_all_retries_exhausted(tmp_path, monkeypatch):
    monkeypatch.setattr("mhd_pos_benchmark.adapters.gemini.time.sleep", lambda _: None)
    responses = [
        FakeResponse("bad"),
        FakeResponse("bad"),
    ]
    adapter = _make_adapter(tmp_path, responses, max_retries=2)
    doc = _make_document(1)
    with pytest.raises(RuntimeError, match="Failed after 2 attempts"):
        adapter.predict(doc)
