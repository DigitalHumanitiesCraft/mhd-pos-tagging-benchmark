"""Tests for the generic CLI adapter.

Mocks subprocess.run so no real CLI tool is needed.
"""

from __future__ import annotations

import json
import subprocess
import uuid
from pathlib import Path

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

    def test_prompt_passed_via_stdin(self, monkeypatch, tmp_path):
        """Custom CLI adapter sends prompt via stdin."""
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append((cmd, kwargs))
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout='["NOM"]', stderr="",
            )

        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.subprocess.run", fake_run)
        adapter = _make_adapter(monkeypatch, tmp_path, cli_cmd="gemini -p")
        doc = _make_document(1)
        adapter.predict(doc)

        cmd, kwargs = calls[0]
        # Prompt content goes via stdin (input kwarg)
        stdin_text = kwargs["input"]
        assert "Tag each word" in stdin_text
        assert "Middle High German" in stdin_text

    def test_system_prompt_embedded_in_stdin(self, monkeypatch, tmp_path):
        """System prompt is embedded in the stdin prompt (task-first)."""
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

        stdin_text = calls[0]["input"]
        # Task comes first (task-first structure for agentic CLIs)
        task_pos = stdin_text.index("Tag each word")
        ref_pos = stdin_text.index("REFERENCE")
        assert task_pos < ref_pos
        # System prompt content
        assert "Valid Tags" in stdin_text
        assert "NOM" in stdin_text
        assert "VRB" in stdin_text
        # User prompt content
        assert "wort0" in stdin_text

    def test_stdin_used_for_prompt(self, monkeypatch, tmp_path):
        """Generic CLI sends prompt via stdin (avoids argument-length limits)."""
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

        assert "input" in calls[0]
        assert "Tag each word" in calls[0]["input"]

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

    def test_no_preset_no_cli_cmd_raises(self, monkeypatch, tmp_path):
        from mhd_pos_benchmark.adapters.generic_cli import GenericCliAdapter

        with pytest.raises(ValueError, match="--preset or --cli-cmd"):
            GenericCliAdapter(cache_dir=tmp_path)

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
            calls.append((cmd, kwargs))
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

        cmd, kwargs = calls[0]
        # copilot resolved to /usr/bin/fakecli by mock, then -p gets empty string
        assert "-p" in cmd
        assert "-s" in cmd
        assert "--no-color" in cmd
        # Prompt via stdin
        assert "Tag each word" in kwargs["input"]

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


class TestWorkingDirectoryIsolation:
    """Agentic CLIs read project instruction files from their working directory.

    Measured 2026-08-18: a `claude -p` call started inside this repository could
    answer questions about the benchmark's own corpus and tagset, and carried
    ~25k tokens of harness context per chunk. Running in an empty directory
    removes both.
    """

    def _capture_cwd(self, monkeypatch):
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(kwargs.get("cwd"))
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout='["NOM"]', stderr="",
            )

        monkeypatch.setattr("mhd_pos_benchmark.adapters.generic_cli.subprocess.run", fake_run)
        return calls

    def test_runs_in_empty_directory_by_default(self, monkeypatch, tmp_path):
        calls = self._capture_cwd(monkeypatch)
        adapter = _make_adapter(monkeypatch, tmp_path)
        adapter.predict(_make_document(1))

        cwd = calls[0]
        assert cwd is not None
        assert list(Path(cwd).iterdir()) == []
        assert Path(cwd).resolve() != Path.cwd().resolve()

    def test_same_directory_reused_across_chunks(self, monkeypatch, tmp_path):
        calls = self._capture_cwd(monkeypatch)
        adapter = _make_adapter(monkeypatch, tmp_path, chunk_size=1)
        adapter.predict(_make_document(3))

        assert len(calls) == 3
        assert len(set(calls)) == 1

    def test_isolation_can_be_disabled(self, monkeypatch, tmp_path):
        calls = self._capture_cwd(monkeypatch)
        adapter = _make_adapter(monkeypatch, tmp_path, isolate_cwd=False)
        adapter.predict(_make_document(1))

        assert calls[0] is None


class TestExecutableResolution:
    """The benchmark must never measure an editor launcher or a mangled prompt."""

    def test_skips_editor_shim_for_the_real_cli(self, monkeypatch, tmp_path):
        from mhd_pos_benchmark.doctor import resolve_real_executable

        shim = r"C:\Users\x\AppData\Roaming\Code\User\globalStorage\copilot.CMD"
        real = r"C:\Users\x\AppData\Roaming\npm\copilot.CMD"

        def fake_which(name, path=None):
            if path is None:
                return shim
            return real if "npm" in path else None

        monkeypatch.setattr("mhd_pos_benchmark.doctor.shutil.which", fake_which)
        monkeypatch.setenv("PATH", r"C:\Users\x\AppData\Roaming\npm")
        assert resolve_real_executable("copilot") == real

    def test_returns_none_when_only_a_shim_exists(self, monkeypatch):
        from mhd_pos_benchmark.doctor import resolve_real_executable

        shim = r"C:\Users\x\AppData\Roaming\Code\User\globalStorage\copilot.CMD"
        monkeypatch.setattr(
            "mhd_pos_benchmark.doctor.shutil.which",
            lambda name, path=None: shim if path is None else None,
        )
        monkeypatch.setenv("PATH", r"C:\some\dir")
        assert resolve_real_executable("copilot") is None

    def test_npm_wrapper_is_unwrapped_to_node(self, monkeypatch, tmp_path):
        """cmd.exe truncated the multi-line prompt to its first line."""
        from mhd_pos_benchmark.adapters.generic_cli import _npm_shim_launcher

        script = tmp_path / "node_modules" / "@github" / "copilot" / "npm-loader.js"
        script.parent.mkdir(parents=True)
        script.write_text("// entry", encoding="utf-8")
        wrapper = tmp_path / "copilot.CMD"
        wrapper.write_text(
            '"%_prog%" "%dp0%\\node_modules\\@github\\copilot\\npm-loader.js" %*\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "mhd_pos_benchmark.adapters.generic_cli.shutil.which",
            lambda name, path=None: "/usr/bin/node",
        )
        launcher = _npm_shim_launcher(str(wrapper))
        assert launcher is not None
        assert launcher[0] == "/usr/bin/node"
        assert launcher[1].endswith("npm-loader.js")

    def test_non_wrapper_is_left_alone(self, tmp_path):
        from mhd_pos_benchmark.adapters.generic_cli import _npm_shim_launcher

        assert _npm_shim_launcher(r"C:\Users\x\.local\bin\claude.EXE") is None

    def test_stdin_presets_keep_the_wrapper(self, monkeypatch, tmp_path):
        """Only argument delivery hits the cmd.exe quoting problem."""
        monkeypatch.setattr(
            "mhd_pos_benchmark.adapters.generic_cli.shutil.which",
            lambda name, path=None: r"C:\npm\codex.CMD",
        )
        from mhd_pos_benchmark.adapters.generic_cli import GenericCliAdapter

        adapter = GenericCliAdapter(preset="codex", cache_dir=tmp_path)
        cmd, stdin = adapter._build_command("Tag each word.")
        assert cmd[0] == r"C:\npm\codex.CMD"
        assert stdin is not None


class TestTimeout:
    """A 1364-token chunk took 363 s in testing; a fixed 300 s would kill it."""

    def test_timeout_scales_with_chunk_size(self, monkeypatch, tmp_path):
        adapter = _make_adapter(monkeypatch, tmp_path, chunk_size=1364)
        assert adapter._timeout >= 363

    def test_small_chunks_keep_the_floor(self, monkeypatch, tmp_path):
        adapter = _make_adapter(monkeypatch, tmp_path, chunk_size=200)
        assert adapter._timeout == 300

    def test_explicit_timeout_wins(self, monkeypatch, tmp_path):
        adapter = _make_adapter(monkeypatch, tmp_path, chunk_size=1364, timeout=60)
        assert adapter._timeout == 60


class TestPresetCommands:
    def test_claude_preset_carries_both_isolation_flags(self):
        """--tools and --strict-mcp-config only reduce the prompt together."""
        from mhd_pos_benchmark.adapters.cli_presets import get_preset

        preset = get_preset("claude")
        assert "--tools" in preset.command
        assert "--strict-mcp-config" in preset.command
        assert preset.isolate_cwd

    def test_model_with_spaces_stays_one_argument(self, monkeypatch, tmp_path):
        """Antigravity model names look like 'Gemini 3.1 Pro (High)'."""
        monkeypatch.setattr(
            "mhd_pos_benchmark.adapters.generic_cli.shutil.which", lambda _: "/usr/bin/agy"
        )
        from mhd_pos_benchmark.adapters.generic_cli import GenericCliAdapter

        adapter = GenericCliAdapter(
            preset="antigravity", model="Gemini 3.1 Pro (High)", cache_dir=tmp_path,
        )
        cmd, _ = adapter._build_command("Tag each word.")
        assert "Gemini 3.1 Pro (High)" in cmd

    def test_empty_tools_flag_survives_parsing(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "mhd_pos_benchmark.adapters.generic_cli.shutil.which", lambda _: "/usr/bin/claude"
        )
        from mhd_pos_benchmark.adapters.generic_cli import GenericCliAdapter

        adapter = GenericCliAdapter(preset="claude", cache_dir=tmp_path)
        cmd, _ = adapter._build_command("Tag each word.")
        assert cmd[cmd.index("--tools") + 1] == ""

    def test_unknown_preset_lists_available(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "mhd_pos_benchmark.adapters.generic_cli.shutil.which", lambda _: "/usr/bin/x"
        )
        from mhd_pos_benchmark.adapters.generic_cli import GenericCliAdapter

        with pytest.raises(ValueError, match="antigravity"):
            GenericCliAdapter(preset="nope", cache_dir=tmp_path)


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

    def test_cli_adapter_requires_preset_or_cli_cmd(self):
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
        assert "--preset" in result.output or "--cli-cmd" in result.output
