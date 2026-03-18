"""Tests for the generic API adapter.

Mocks the openai SDK so no real API key or package install is needed.
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


# --- Fake OpenAI SDK ---


class FakeMessage:
    def __init__(self, content: str | None):
        self.content = content


class FakeChoice:
    def __init__(self, message: FakeMessage):
        self.message = message


class FakeCompletion:
    def __init__(self, content: str | None):
        self.choices = [FakeChoice(FakeMessage(content))]


class FakeCompletions:
    def __init__(self, responses: list[FakeCompletion]):
        self._responses = responses
        self._call_count = 0

    def create(self, **kwargs):
        idx = self._call_count
        self._call_count += 1
        return self._responses[idx]


class FakeChat:
    def __init__(self, completions: FakeCompletions):
        self.completions = completions


class FakeOpenAI:
    def __init__(self, api_key: str = "test", base_url: str = ""):
        self.chat = None  # set by _make_adapter


@pytest.fixture(autouse=True)
def mock_openai(monkeypatch):
    """Install fake openai module so GenericApiAdapter can be imported without the real SDK."""
    openai_mod = types.ModuleType("openai")
    openai_mod.OpenAI = FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", openai_mod)


def _make_adapter(tmp_path, responses, **kwargs):
    """Create a GenericApiAdapter with mocked client."""
    from mhd_pos_benchmark.adapters.generic_api import GenericApiAdapter

    adapter = GenericApiAdapter(api_key="test-key", cache_dir=tmp_path, **kwargs)
    completions = FakeCompletions(responses)
    adapter._client.chat = FakeChat(completions)
    return adapter


def test_name_uses_model(tmp_path):
    from mhd_pos_benchmark.adapters.generic_api import GenericApiAdapter

    adapter = GenericApiAdapter(api_key="test-key", model="gpt-4o", cache_dir=tmp_path)
    assert adapter.name == "gpt-4o"


def test_name_default_model(tmp_path):
    from mhd_pos_benchmark.adapters.generic_api import GenericApiAdapter

    adapter = GenericApiAdapter(api_key="test-key", cache_dir=tmp_path)
    # Default provider is openai, default model is gpt-4o
    assert adapter.name == "gpt-4o"


def test_provider_gemini_default_model(tmp_path):
    from mhd_pos_benchmark.adapters.generic_api import GenericApiAdapter

    adapter = GenericApiAdapter(
        api_key="test-key", provider="gemini", cache_dir=tmp_path,
    )
    assert adapter.name == "gemini-2.5-flash"


def test_predict_basic(tmp_path):
    tags = ["NOM", "NOM", "NOM", "NOM", "NOM"]
    responses = [FakeCompletion(json.dumps(tags))]
    adapter = _make_adapter(tmp_path, responses)
    doc = _make_document(5)
    result = adapter.predict(doc)
    assert result == tags


def test_caching(tmp_path):
    tags = ["NOM", "NOM", "NOM", "NOM", "NOM"]
    responses = [FakeCompletion(json.dumps(tags))]
    adapter = _make_adapter(tmp_path, responses)
    doc = _make_document(5)

    result1 = adapter.predict(doc)
    result2 = adapter.predict(doc)  # cache hit, no second API call

    assert result1 == result2 == tags


def test_chunking(tmp_path):
    responses = [
        FakeCompletion(json.dumps(["NOM", "NOM", "NOM"])),
        FakeCompletion(json.dumps(["NOM", "NOM"])),
    ]
    adapter = _make_adapter(tmp_path, responses, chunk_size=3)
    doc = _make_document(5)
    result = adapter.predict(doc)

    assert result == ["NOM"] * 5


def test_no_api_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from mhd_pos_benchmark.adapters.generic_api import GenericApiAdapter

    with pytest.raises(OSError, match="No API key"):
        GenericApiAdapter()


def test_local_endpoint_no_key_needed(tmp_path):
    """Local endpoints (ollama, vLLM) don't require an API key."""
    from mhd_pos_benchmark.adapters.generic_api import GenericApiAdapter

    adapter = GenericApiAdapter(
        api_base="http://localhost:11434/v1",
        model="llama3",
        cache_dir=tmp_path,
    )
    assert adapter.name == "llama3"


def test_null_content_retries(tmp_path, monkeypatch):
    """Filtered response (content=None) should trigger retry."""
    monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_api.time.sleep", lambda _: None)
    responses = [
        FakeCompletion(None),  # filtered
        FakeCompletion(json.dumps(["NOM"])),
    ]
    adapter = _make_adapter(tmp_path, responses, max_retries=2)
    doc = _make_document(1)
    result = adapter.predict(doc)
    assert result == ["NOM"]


def test_bad_json_retries(tmp_path, monkeypatch):
    monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_api.time.sleep", lambda _: None)
    responses = [
        FakeCompletion("not valid json"),
        FakeCompletion(json.dumps(["NOM"])),
    ]
    adapter = _make_adapter(tmp_path, responses, max_retries=2)
    doc = _make_document(1)
    result = adapter.predict(doc)
    assert result == ["NOM"]


def test_all_retries_exhausted(tmp_path, monkeypatch):
    monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_api.time.sleep", lambda _: None)
    responses = [
        FakeCompletion("bad"),
        FakeCompletion("bad"),
    ]
    adapter = _make_adapter(tmp_path, responses, max_retries=2)
    doc = _make_document(1)
    with pytest.raises(RuntimeError, match="Failed after 2 attempts"):
        adapter.predict(doc)
