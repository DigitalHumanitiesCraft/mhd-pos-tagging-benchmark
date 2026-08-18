"""Tests for doctor.py — diagnostics and corpus auto-detection."""

from __future__ import annotations

import json

from mhd_pos_benchmark.doctor import (
    _API_KEYS,
    _CLI_TOOLS,
    CheckResult,
    cached_document_ids,
    check_api_keys,
    check_cli_tools,
    check_corpus,
    check_openai_sdk,
    check_python_version,
    find_corpus_dir,
    is_shim,
    suggest_commands,
)


class TestFindCorpusDir:
    def test_finds_nested_path(self, tmp_path):
        """Finds the standard nested ReM download structure."""
        corpus = tmp_path / "ReM-v2.1_coraxml" / "ReM-v2.1_coraxml" / "cora-xml"
        corpus.mkdir(parents=True)
        (corpus / "M001.xml").write_text("<text/>")
        assert find_corpus_dir(tmp_path) == corpus

    def test_finds_single_level(self, tmp_path):
        corpus = tmp_path / "ReM-v2.1_coraxml" / "cora-xml"
        corpus.mkdir(parents=True)
        (corpus / "M001.xml").write_text("<text/>")
        assert find_corpus_dir(tmp_path) == corpus

    def test_finds_corpus_dir(self, tmp_path):
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        (corpus / "M001.xml").write_text("<text/>")
        assert find_corpus_dir(tmp_path) == corpus

    def test_finds_bare_cora_xml(self, tmp_path):
        corpus = tmp_path / "cora-xml"
        corpus.mkdir()
        (corpus / "M001.xml").write_text("<text/>")
        assert find_corpus_dir(tmp_path) == corpus

    def test_returns_none_if_empty(self, tmp_path):
        assert find_corpus_dir(tmp_path) is None

    def test_returns_none_if_dir_exists_but_no_xml(self, tmp_path):
        (tmp_path / "corpus").mkdir()
        assert find_corpus_dir(tmp_path) is None

    def test_priority_corpus_over_nested(self, tmp_path):
        """./corpus/ is preferred over the nested path."""
        (tmp_path / "corpus").mkdir()
        (tmp_path / "corpus" / "M001.xml").write_text("<text/>")
        nested = tmp_path / "ReM-v2.1_coraxml" / "ReM-v2.1_coraxml" / "cora-xml"
        nested.mkdir(parents=True)
        (nested / "M001.xml").write_text("<text/>")
        assert find_corpus_dir(tmp_path) == tmp_path / "corpus"


class TestChecks:
    def test_python_version_ok(self):
        result = check_python_version()
        assert result.status == "ok"  # we're running on 3.13+

    def test_corpus_not_found(self, tmp_path):
        result = check_corpus(tmp_path)
        assert result.status == "fail"
        assert "Not found" in result.message
        assert "rem" in result.fix_hint.lower()

    def test_corpus_found(self, tmp_path):
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        for i in range(3):
            (corpus / f"M{i:03d}.xml").write_text("<text/>")
        result = check_corpus(tmp_path)
        assert result.status == "ok"
        assert "3 documents" in result.message

    def test_openai_sdk_installed(self):
        # openai should be installed in dev environment
        result = check_openai_sdk()
        assert result.status == "ok"

    def test_api_keys(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy_test_key_12345")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        results = check_api_keys()
        gemini = next(r for r in results if r.name == "GEMINI_API_KEY")
        openai = next(r for r in results if r.name == "OPENAI_API_KEY")
        assert gemini.status == "ok"
        assert "AIz..." in gemini.message  # masked
        assert openai.status == "warn"

    def test_cli_tools(self, monkeypatch):
        monkeypatch.setattr("mhd_pos_benchmark.doctor.shutil.which", lambda x: "/usr/bin/claude" if x == "claude" else None)
        results = check_cli_tools()
        claude = next(r for r in results if r.name == "Claude")
        codex = next(r for r in results if r.name == "Codex")
        assert claude.status == "ok"
        assert codex.status == "warn"


class TestSuggestCommands:
    def _make_results(self, cli_found=None, api_found=None, cached=None):
        # Built from the real tables: suggest_commands zips its results against
        # _CLI_TOOLS / _API_KEYS positionally, so a hand-written list silently
        # misaligns as soon as a tool is added.
        cli_found = cli_found or []
        api_found = api_found or []
        cached = cached or []
        cli_results = [
            CheckResult(display, "ok" if display in cli_found else "warn", "")
            for _, display, _, _ in _CLI_TOOLS
        ]
        api_results = [
            CheckResult(env, "ok" if env in api_found else "warn", "")
            for env, _, _ in _API_KEYS
        ]
        cache_results = [CheckResult(m, "ok", "3 docs") for m in cached]
        return cli_results, api_results, cache_results

    def test_cli_and_api_available(self):
        cli_r, api_r, cache_r = self._make_results(
            cli_found=["Claude", "Gemini"],
            api_found=["GEMINI_API_KEY"],
        )
        suggestions = suggest_commands(cli_r, api_r, cache_r, corpus_found=True)
        assert len(suggestions) == 2  # 1 CLI + 1 API
        assert "claude" in suggestions[0].lower()
        assert "gemini" in suggestions[1].lower()

    def test_only_cli(self):
        cli_r, api_r, cache_r = self._make_results(cli_found=["Gemini"])
        suggestions = suggest_commands(cli_r, api_r, cache_r, corpus_found=True)
        assert len(suggestions) == 1
        assert "gemini" in suggestions[0].lower()

    def _write_cache(self, cache_dir, model, doc_ids):
        model_dir = cache_dir / model
        model_dir.mkdir(parents=True)
        lines = [
            json.dumps({"document_id": d, "predictions": ["NOM"], "config_hash": "x"})
            for d in doc_ids
        ]
        (model_dir / "predictions.jsonl").write_text("\n".join(lines), encoding="utf-8")

    def test_cached_models_adds_compare(self, tmp_path):
        self._write_cache(tmp_path, "model-a", ["M001", "M002"])
        self._write_cache(tmp_path, "model-b", ["M002", "M003"])
        cli_r, api_r, cache_r = self._make_results(
            cli_found=["Claude"],
            cached=["model-a", "model-b"],
        )
        suggestions = suggest_commands(
            cli_r, api_r, cache_r, corpus_found=True, cache_dir=tmp_path,
        )
        compare = next(s for s in suggestions if "mhd-bench compare" in s)
        assert "model-a,model-b" in compare
        assert "1 shared documents" in compare

    def test_disjoint_caches_do_not_suggest_compare(self, tmp_path):
        """Comparing caches with no shared documents aborts on the first miss."""
        self._write_cache(tmp_path, "model-a", ["M001"])
        self._write_cache(tmp_path, "model-b", ["M999"])
        cli_r, api_r, cache_r = self._make_results(cached=["model-a", "model-b"])
        suggestions = suggest_commands(
            cli_r, api_r, cache_r, corpus_found=True, cache_dir=tmp_path,
        )
        assert not any("mhd-bench compare" in s for s in suggestions)
        assert any("share no documents" in s for s in suggestions)

    def test_nothing_found(self):
        cli_r, api_r, cache_r = self._make_results()
        suggestions = suggest_commands(cli_r, api_r, cache_r, corpus_found=True)
        assert len(suggestions) == 1
        assert "No taggers detected" in suggestions[0]
        assert "aistudio.google.com" in suggestions[0]

    def test_no_corpus_returns_empty(self):
        cli_r, api_r, cache_r = self._make_results(cli_found=["Claude"])
        suggestions = suggest_commands(cli_r, api_r, cache_r, corpus_found=False)
        assert suggestions == []

    def test_max_two_evaluate_suggestions(self):
        """Even with many tools, max 2 evaluate suggestions."""
        cli_r, api_r, cache_r = self._make_results(
            cli_found=["Claude", "Gemini", "Codex"],
            api_found=["GEMINI_API_KEY", "OPENAI_API_KEY"],
        )
        suggestions = suggest_commands(cli_r, api_r, cache_r, corpus_found=True)
        evaluate_suggestions = [s for s in suggestions if "evaluate" in s]
        assert len(evaluate_suggestions) <= 2


class TestShimDetection:
    """The VS Code Copilot extension ships a launcher that shadows the real CLI."""

    def test_vscode_copilot_shim(self):
        path = (
            r"c:\Users\x\AppData\Roaming\Code\User\globalStorage"
            r"\github.copilot-chat\copilotCli\copilot.ps1"
        )
        assert is_shim(path)

    def test_real_cli_is_not_a_shim(self):
        assert not is_shim(r"C:\Users\x\.local\bin\claude.EXE")
        assert not is_shim("/usr/local/bin/copilot")

    def test_shim_reported_as_warning(self, monkeypatch):
        """Only a shim on PATH must not read as an installed tool."""
        shim = r"C:\Users\x\AppData\Roaming\Code\User\globalStorage\cli.ps1"
        monkeypatch.setattr(
            "mhd_pos_benchmark.doctor.shutil.which",
            lambda name, path=None: shim if path is None else None,
        )
        results = check_cli_tools()
        assert all(r.status == "warn" for r in results)
        assert all("editor shim" in r.message for r in results)

    def test_real_cli_behind_a_shim_is_found(self, monkeypatch):
        shim = r"C:\Users\x\AppData\Roaming\Code\User\globalStorage\copilot.CMD"
        real = r"C:\Users\x\AppData\Roaming\npm\copilot.CMD"
        monkeypatch.setenv("PATH", r"C:\Users\x\AppData\Roaming\npm")
        monkeypatch.setattr(
            "mhd_pos_benchmark.doctor.shutil.which",
            lambda name, path=None: shim if path is None else real,
        )
        results = check_cli_tools()
        assert all(r.status == "ok" for r in results)
        assert all(r.message == real for r in results)


class TestCachedDocumentIds:
    def test_reads_ids(self, tmp_path):
        model_dir = tmp_path / "m"
        model_dir.mkdir()
        (model_dir / "predictions.jsonl").write_text(
            '{"document_id": "M001", "predictions": ["NOM"]}\n'
            "\n"
            '{"document_id": "M002", "predictions": ["VRB"]}\n',
            encoding="utf-8",
        )
        assert cached_document_ids("m", tmp_path) == {"M001", "M002"}

    def test_missing_cache_is_empty(self, tmp_path):
        assert cached_document_ids("nope", tmp_path) == set()

    def test_skips_corrupt_lines(self, tmp_path):
        model_dir = tmp_path / "m"
        model_dir.mkdir()
        (model_dir / "predictions.jsonl").write_text(
            'not json\n{"document_id": "M001"}\n', encoding="utf-8"
        )
        assert cached_document_ids("m", tmp_path) == {"M001"}


class TestDoctorCli:
    def test_doctor_runs(self):
        from click.testing import CliRunner

        from mhd_pos_benchmark.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "System Check" in result.output
        assert "Python" in result.output
