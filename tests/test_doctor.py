"""Tests for doctor.py — diagnostics and corpus auto-detection."""

from __future__ import annotations

from mhd_pos_benchmark.doctor import (
    CheckResult,
    check_api_keys,
    check_cli_tools,
    check_corpus,
    check_openai_sdk,
    check_python_version,
    find_corpus_dir,
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
        cli_found = cli_found or []
        api_found = api_found or []
        cached = cached or []
        cli_results = [
            CheckResult(name, "ok" if name in cli_found else "warn", "")
            for _, name, _, _ in [
                ("claude", "Claude", "", ""),
                ("gemini", "Gemini", "", ""),
                ("codex", "Codex", "", ""),
                ("copilot", "Copilot", "", ""),
            ]
        ]
        api_results = [
            CheckResult(env, "ok" if env in api_found else "warn", "")
            for env, _, _ in [
                ("GEMINI_API_KEY", "gemini", ""),
                ("OPENAI_API_KEY", "openai", ""),
                ("MISTRAL_API_KEY", "mistral", ""),
                ("GROQ_API_KEY", "groq", ""),
            ]
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

    def test_cached_models_adds_compare(self):
        cli_r, api_r, cache_r = self._make_results(
            cli_found=["Claude"],
            cached=["claude-opus", "gemini-2.5-pro"],
        )
        suggestions = suggest_commands(cli_r, api_r, cache_r, corpus_found=True)
        assert any("compare" in s for s in suggestions)

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


class TestDoctorCli:
    def test_doctor_runs(self):
        from click.testing import CliRunner

        from mhd_pos_benchmark.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "System Check" in result.output
        assert "Python" in result.output
