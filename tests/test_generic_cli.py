"""Tests for the generic CLI adapter.

Mocks subprocess.run so no real CLI tool is needed.
"""

from __future__ import annotations

import json
import subprocess
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


def _make_adapter(monkeypatch, tmp_path, cli_cmd="fakecli -p", **kwargs):
    """Create GenericCliAdapter with mocked shutil.which."""
    monkeypatch.setattr(
        "mhd_pos_benchmark.adapters.generic_cli.shutil.which", lambda _: "/usr/bin/fakecli"
    )
    from mhd_pos_benchmark.adapters.generic_cli import GenericCliAdapter

    return GenericCliAdapter(cli_cmd=cli_cmd, cache_dir=tmp_path, **kwargs)


class TestGenericCliAdapter:
    def test_predict_basic(self, monkeypatch, tmp_path):
        tags = ["NOM", "NOM", "NOM", "NOM", "NOM"]
        monkeypatch.setattr(
            "mhd_pos_benchmark.adapters.generic_cli.subprocess.run",
            lambda *a, **kw: subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout=json.dumps(tags), stderr="",
            ),
        )
        adapter = _make_adapter(monkeypatch, tmp_path)
        doc = _make_document(5)
        result = adapter.predict(doc)
        assert result == tags

    def test_name_defaults_to_cli_executable(self, monkeypatch, tmp_path):
        adapter = _make_adapter(monkeypatch, tmp_path, cli_cmd="gemini -p")
        assert adapter.name == "cli-gemini"

    def test_name_uses_model_name(self, monkeypatch, tmp_path):
        adapter = _make_adapter(
            monkeypatch, tmp_path, cli_cmd="gemini -p", model_name="gemini-2.5-pro"
        )
        assert adapter.name == "gemini-2.5-pro"

    def test_prompt_passed_as_last_argument(self, monkeypatch, tmp_path):
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout='["NOM"]', stderr="",
            )

        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.subprocess.run", fake_run)
        adapter = _make_adapter(monkeypatch, tmp_path, cli_cmd="gemini -p")
        doc = _make_document(1)
        adapter.predict(doc)

        cmd = calls[0]
        assert cmd[0] == "gemini"
        assert cmd[1] == "-p"
        # Last argument is the combined prompt (system + user)
        assert "Tag each word" in cmd[-1]
        assert "Middle High German" in cmd[-1]

    def test_system_prompt_embedded_in_user_prompt(self, monkeypatch, tmp_path):
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout='["NOM"]', stderr="",
            )

        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.subprocess.run", fake_run)
        adapter = _make_adapter(monkeypatch, tmp_path)
        doc = _make_document(1)
        adapter.predict(doc)

        combined_prompt = calls[0][-1]
        # System prompt content
        assert "Valid Tags" in combined_prompt
        assert "NOM" in combined_prompt
        assert "VRB" in combined_prompt
        # User prompt content
        assert "Tag each word" in combined_prompt
        assert "wort0" in combined_prompt

    def test_no_stdin_used(self, monkeypatch, tmp_path):
        """Generic CLI passes prompt as argument, not stdin."""
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(kwargs)
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout='["NOM"]', stderr="",
            )

        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.subprocess.run", fake_run)
        adapter = _make_adapter(monkeypatch, tmp_path)
        doc = _make_document(1)
        adapter.predict(doc)

        # No 'input' kwarg — prompt goes via cmd args, not stdin
        assert "input" not in calls[0]

    def test_retry_on_bad_response(self, monkeypatch, tmp_path):
        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.time.sleep", lambda _: None)
        attempt = {"n": 0}

        def fake_run(cmd, **kwargs):
            attempt["n"] += 1
            if attempt["n"] == 1:
                return subprocess.CompletedProcess(
                    args=[], returncode=0,
                    stdout='["BOGUS"]', stderr="",
                )
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout='["NOM"]', stderr="",
            )

        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.subprocess.run", fake_run)
        adapter = _make_adapter(monkeypatch, tmp_path, max_retries=2)
        doc = _make_document(1)
        result = adapter.predict(doc)

        assert result == ["NOM"]
        assert attempt["n"] == 2

    def test_retry_on_empty_stdout(self, monkeypatch, tmp_path):
        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.time.sleep", lambda _: None)
        attempt = {"n": 0}

        def fake_run(cmd, **kwargs):
            attempt["n"] += 1
            if attempt["n"] == 1:
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="", stderr="",
                )
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout='["NOM"]', stderr="",
            )

        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.subprocess.run", fake_run)
        adapter = _make_adapter(monkeypatch, tmp_path, max_retries=2)
        doc = _make_document(1)
        result = adapter.predict(doc)

        assert result == ["NOM"]

    def test_retry_on_nonzero_exit(self, monkeypatch, tmp_path):
        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.time.sleep", lambda _: None)
        monkeypatch.setattr(
            "mhd_pos_benchmark.adapters.generic_cli.subprocess.run",
            lambda *a, **kw: subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="error",
            ),
        )
        adapter = _make_adapter(monkeypatch, tmp_path, max_retries=2)
        doc = _make_document(1)

        with pytest.raises(RuntimeError, match="Failed after 2 attempts"):
            adapter.predict(doc)

    def test_availability_check_fails(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "mhd_pos_benchmark.adapters.generic_cli.shutil.which", lambda _: None
        )
        from mhd_pos_benchmark.adapters.generic_cli import GenericCliAdapter

        with pytest.raises(OSError, match="not found on PATH"):
            GenericCliAdapter(cli_cmd="nonexistent-tool -p", cache_dir=tmp_path)

    def test_empty_cli_cmd_raises(self, monkeypatch, tmp_path):
        from mhd_pos_benchmark.adapters.generic_cli import GenericCliAdapter

        with pytest.raises(ValueError, match="must not be empty"):
            GenericCliAdapter(cli_cmd="", cache_dir=tmp_path)

    def test_caching(self, monkeypatch, tmp_path):
        call_count = {"n": 0}
        tags = ["NOM", "NOM", "NOM", "NOM", "NOM"]

        def fake_run(cmd, **kwargs):
            call_count["n"] += 1
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout=json.dumps(tags), stderr="",
            )

        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.subprocess.run", fake_run)
        adapter = _make_adapter(monkeypatch, tmp_path)
        doc = _make_document(5)

        result1 = adapter.predict(doc)
        result2 = adapter.predict(doc)

        assert result1 == result2 == tags
        assert call_count["n"] == 1

    def test_chunking(self, monkeypatch, tmp_path):
        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.time.sleep", lambda _: None)
        call_count = {"n": 0}
        responses = ['["NOM", "NOM", "NOM"]', '["NOM", "NOM"]']

        def fake_run(cmd, **kwargs):
            idx = call_count["n"]
            call_count["n"] += 1
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout=responses[idx], stderr="",
            )

        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.subprocess.run", fake_run)
        adapter = _make_adapter(monkeypatch, tmp_path, chunk_size=3, delay=0)
        doc = _make_document(5)
        result = adapter.predict(doc)

        assert result == ["NOM"] * 5
        assert call_count["n"] == 2

    def test_multi_word_cli_cmd_parsed(self, monkeypatch, tmp_path):
        """'copilot -p -s --no-color' should be split into 4 parts."""
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout='["NOM"]', stderr="",
            )

        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.subprocess.run", fake_run)
        adapter = _make_adapter(
            monkeypatch, tmp_path, cli_cmd="copilot -p -s --no-color"
        )
        doc = _make_document(1)
        adapter.predict(doc)

        cmd = calls[0]
        assert cmd[0] == "copilot"
        assert cmd[1] == "-p"
        assert cmd[2] == "-s"
        assert cmd[3] == "--no-color"
        # Last element is the prompt
        assert "Tag each word" in cmd[4]

    def test_handles_text_around_json(self, monkeypatch, tmp_path):
        """CLI might print extra text around the JSON array."""
        monkeypatch.setattr(
            "mhd_pos_benchmark.adapters.generic_cli.subprocess.run",
            lambda *a, **kw: subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout='Here are the tags:\n["NOM", "VRB"]\nHope that helps!',
                stderr="",
            ),
        )
        adapter = _make_adapter(monkeypatch, tmp_path)
        doc = _make_document(2)
        result = adapter.predict(doc)
        assert result == ["NOM", "VRB"]


class TestGenericCliCli:
    """Test CLI integration for --adapter cli."""

    def test_evaluate_cli_adapter(self, monkeypatch, tmp_path):
        from pathlib import Path

        from click.testing import CliRunner

        from mhd_pos_benchmark.cli import cli

        # Mock the generic CLI adapter to avoid real subprocess calls
        monkeypatch.setattr(
            "mhd_pos_benchmark.adapters.generic_cli.shutil.which", lambda _: "/usr/bin/fakecli"
        )
        monkeypatch.setattr(
            "mhd_pos_benchmark.adapters.generic_cli.subprocess.run",
            lambda *a, **kw: subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout='["NOM", "VRB", "PRP", "DET", "NOM", "PRP", "DET"]',
                stderr="",
            ),
        )

        fixtures = Path(__file__).parent / "fixtures"
        runner = CliRunner()
        result = runner.invoke(cli, [
            "evaluate", str(fixtures),
            "--adapter", "cli",
            "--cli-cmd", "fakecli -p",
            "--model", "test-model",
        ])
        assert result.exit_code == 0, result.output
        assert "test-model" in result.output
        assert "Accuracy" in result.output

    def test_cli_adapter_requires_cli_cmd(self):
        from pathlib import Path

        from click.testing import CliRunner

        from mhd_pos_benchmark.cli import cli

        fixtures = Path(__file__).parent / "fixtures"
        runner = CliRunner()
        result = runner.invoke(cli, [
            "evaluate", str(fixtures),
            "--adapter", "cli",
        ])
        assert result.exit_code != 0
        assert "requires --cli-cmd" in result.output
