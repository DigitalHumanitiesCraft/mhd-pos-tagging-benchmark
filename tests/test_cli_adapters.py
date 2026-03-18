"""Tests for CLI-based LLM adapters.

Mocks subprocess.run so no real CLI tool is needed.
Each test uses tmp_path for cache isolation.
"""

from __future__ import annotations

import json
import subprocess
import uuid

import pytest

from mhd_pos_benchmark.adapters.prompt_template import parse_tag_response
from mhd_pos_benchmark.data.corpus import Document, Token


# ---------------------------------------------------------------------------
# Shared: parse_tag_response
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_document(n_tokens: int = 5, doc_id: str | None = None) -> Document:
    """Create a minimal Document with mappable tokens and unique ID."""
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


def _make_claude_stdout(tags: list[str]) -> str:
    """Build the JSON envelope that `claude -p --output-format json` returns."""
    return json.dumps({"result": json.dumps(tags)})


def _make_adapter(tmp_path, **kwargs):
    """Create ClaudeCliAdapter with isolated cache, mocking shutil.which."""
    from mhd_pos_benchmark.adapters.claude_cli import ClaudeCliAdapter

    return ClaudeCliAdapter(cache_dir=tmp_path, **kwargs)


# ---------------------------------------------------------------------------
# ClaudeCliAdapter
# ---------------------------------------------------------------------------


def test_predict_basic(monkeypatch, tmp_path):
    monkeypatch.setattr("mhd_pos_benchmark.adapters.claude_cli.shutil.which", lambda _: "/usr/bin/claude")

    tags = ["NOM", "NOM", "NOM", "NOM", "NOM"]
    monkeypatch.setattr(
        "mhd_pos_benchmark.adapters.cli_base.subprocess.run",
        lambda *a, **kw: subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=_make_claude_stdout(tags), stderr="",
        ),
    )

    adapter = _make_adapter(tmp_path)
    doc = _make_document(5)
    result = adapter.predict(doc)

    assert result == tags


def test_command_uses_print_mode(monkeypatch, tmp_path):
    monkeypatch.setattr("mhd_pos_benchmark.adapters.claude_cli.shutil.which", lambda _: "/usr/bin/claude")

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        tags = ["NOM"]
        return subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=_make_claude_stdout(tags), stderr="",
        )

    monkeypatch.setattr("mhd_pos_benchmark.adapters.cli_base.subprocess.run", fake_run)

    adapter = _make_adapter(tmp_path)
    doc = _make_document(1)
    adapter.predict(doc)

    cmd = calls[0][0]
    assert "claude" in cmd
    assert "-p" in cmd
    assert "--output-format" in cmd
    assert "json" in cmd


def test_passes_prompt_via_stdin(monkeypatch, tmp_path):
    monkeypatch.setattr("mhd_pos_benchmark.adapters.claude_cli.shutil.which", lambda _: "/usr/bin/claude")

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=_make_claude_stdout(["NOM"]), stderr="",
        )

    monkeypatch.setattr("mhd_pos_benchmark.adapters.cli_base.subprocess.run", fake_run)

    adapter = _make_adapter(tmp_path)
    doc = _make_document(1)
    adapter.predict(doc)

    assert calls[0][1].get("input") is not None


def test_retry_on_bad_response(monkeypatch, tmp_path):
    monkeypatch.setattr("mhd_pos_benchmark.adapters.claude_cli.shutil.which", lambda _: "/usr/bin/claude")

    attempt = {"n": 0}

    def fake_run(cmd, **kwargs):
        attempt["n"] += 1
        if attempt["n"] == 1:
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout=_make_claude_stdout(["BOGUS"]), stderr="",
            )
        return subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=_make_claude_stdout(["NOM"]), stderr="",
        )

    monkeypatch.setattr("mhd_pos_benchmark.adapters.cli_base.subprocess.run", fake_run)
    monkeypatch.setattr("mhd_pos_benchmark.adapters.cli_base.time.sleep", lambda _: None)

    adapter = _make_adapter(tmp_path, max_retries=2)
    doc = _make_document(1)
    result = adapter.predict(doc)

    assert result == ["NOM"]
    assert attempt["n"] == 2


def test_retry_on_timeout(monkeypatch, tmp_path):
    monkeypatch.setattr("mhd_pos_benchmark.adapters.claude_cli.shutil.which", lambda _: "/usr/bin/claude")

    attempt = {"n": 0}

    def fake_run(cmd, **kwargs):
        attempt["n"] += 1
        if attempt["n"] == 1:
            raise subprocess.TimeoutExpired(cmd=["claude"], timeout=120)
        return subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=_make_claude_stdout(["NOM"]), stderr="",
        )

    monkeypatch.setattr("mhd_pos_benchmark.adapters.cli_base.subprocess.run", fake_run)
    monkeypatch.setattr("mhd_pos_benchmark.adapters.cli_base.time.sleep", lambda _: None)

    adapter = _make_adapter(tmp_path, max_retries=2)
    doc = _make_document(1)
    result = adapter.predict(doc)

    assert result == ["NOM"]


def test_nonzero_exit_retries(monkeypatch, tmp_path):
    monkeypatch.setattr("mhd_pos_benchmark.adapters.claude_cli.shutil.which", lambda _: "/usr/bin/claude")

    monkeypatch.setattr(
        "mhd_pos_benchmark.adapters.cli_base.subprocess.run",
        lambda *a, **kw: subprocess.CompletedProcess(
            args=[], returncode=1,
            stdout="", stderr="Error: something went wrong",
        ),
    )
    monkeypatch.setattr("mhd_pos_benchmark.adapters.cli_base.time.sleep", lambda _: None)

    adapter = _make_adapter(tmp_path, max_retries=2)
    doc = _make_document(1)

    with pytest.raises(RuntimeError, match="Failed after 2 attempts"):
        adapter.predict(doc)


def test_availability_check_fails(monkeypatch, tmp_path):
    monkeypatch.setattr("mhd_pos_benchmark.adapters.claude_cli.shutil.which", lambda _: None)

    from mhd_pos_benchmark.adapters.claude_cli import ClaudeCliAdapter

    with pytest.raises(OSError, match="Claude Code CLI not found"):
        ClaudeCliAdapter(cache_dir=tmp_path)


def test_caching(monkeypatch, tmp_path):
    monkeypatch.setattr("mhd_pos_benchmark.adapters.claude_cli.shutil.which", lambda _: "/usr/bin/claude")

    call_count = {"n": 0}
    tags = ["NOM", "NOM", "NOM", "NOM", "NOM"]

    def fake_run(cmd, **kwargs):
        call_count["n"] += 1
        return subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=_make_claude_stdout(tags), stderr="",
        )

    monkeypatch.setattr("mhd_pos_benchmark.adapters.cli_base.subprocess.run", fake_run)

    adapter = _make_adapter(tmp_path)
    doc = _make_document(5)

    result1 = adapter.predict(doc)
    result2 = adapter.predict(doc)

    assert result1 == result2 == tags
    assert call_count["n"] == 1


def test_chunking(monkeypatch, tmp_path):
    """With chunk_size=3 and 5 tokens, expect 2 subprocess calls."""
    monkeypatch.setattr("mhd_pos_benchmark.adapters.claude_cli.shutil.which", lambda _: "/usr/bin/claude")

    call_count = {"n": 0}
    responses = [
        _make_claude_stdout(["NOM", "NOM", "NOM"]),
        _make_claude_stdout(["NOM", "NOM"]),
    ]

    def fake_run(cmd, **kwargs):
        idx = call_count["n"]
        call_count["n"] += 1
        return subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=responses[idx], stderr="",
        )

    monkeypatch.setattr("mhd_pos_benchmark.adapters.cli_base.subprocess.run", fake_run)
    monkeypatch.setattr("mhd_pos_benchmark.adapters.cli_base.time.sleep", lambda _: None)

    adapter = _make_adapter(tmp_path, chunk_size=3, delay=0)
    doc = _make_document(5)
    result = adapter.predict(doc)

    assert result == ["NOM"] * 5
    assert call_count["n"] == 2


def test_name(monkeypatch, tmp_path):
    monkeypatch.setattr("mhd_pos_benchmark.adapters.claude_cli.shutil.which", lambda _: "/usr/bin/claude")

    from mhd_pos_benchmark.adapters.claude_cli import ClaudeCliAdapter

    adapter = ClaudeCliAdapter(cache_dir=tmp_path)
    assert adapter.name == "claude-cli"
