"""Integration tests for the CLI commands using Click's CliRunner."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from mhd_pos_benchmark.cli import cli

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_basic():
    runner = CliRunner()
    result = runner.invoke(cli, ["parse", str(FIXTURES_DIR)])
    assert result.exit_code == 0
    assert "Parsed 1 documents" in result.output


def test_parse_with_stats():
    runner = CliRunner()
    result = runner.invoke(cli, ["parse", str(FIXTURES_DIR), "--stats"])
    assert result.exit_code == 0
    assert "Corpus Statistics" in result.output
    assert "Documents" in result.output
    assert "Total tokens" in result.output
    assert "HiTS Tags" in result.output


def test_parse_nonexistent_dir():
    runner = CliRunner()
    result = runner.invoke(cli, ["parse", "/nonexistent/path"])
    assert result.exit_code != 0


def test_mapping_show():
    runner = CliRunner()
    result = runner.invoke(cli, ["mapping"])
    assert result.exit_code == 0
    assert "HiTS" in result.output
    assert "MHDBDB" in result.output


def test_mapping_validate():
    runner = CliRunner()
    result = runner.invoke(cli, ["mapping", "--validate", "--corpus-dir", str(FIXTURES_DIR)])
    assert result.exit_code == 0
    assert "All HiTS tags" in result.output


def test_mapping_validate_without_corpus_dir(tmp_path, monkeypatch):
    """Without --corpus-dir and no auto-detectable corpus, gives clear error."""
    monkeypatch.chdir(tmp_path)  # empty dir, no corpus to find
    runner = CliRunner()
    result = runner.invoke(cli, ["mapping", "--validate"])
    assert result.exit_code != 0
    assert "Corpus directory not found" in result.output


def test_evaluate_passthrough():
    runner = CliRunner()
    result = runner.invoke(cli, [
        "evaluate", str(FIXTURES_DIR), "--adapter", "passthrough",
    ])
    assert result.exit_code == 0
    assert "gold-passthrough" in result.output
    assert "Accuracy" in result.output
    # Passthrough should give 100%
    assert "1.0000" in result.output


def test_evaluate_majority():
    runner = CliRunner()
    result = runner.invoke(cli, [
        "evaluate", str(FIXTURES_DIR), "--adapter", "majority",
    ])
    assert result.exit_code == 0
    assert "majority-class" in result.output
    assert "Accuracy" in result.output


def test_evaluate_with_output(tmp_path):
    import json

    runner = CliRunner()
    out = tmp_path / "result.json"
    result = runner.invoke(cli, [
        "evaluate", str(FIXTURES_DIR), "--adapter", "passthrough",
        "--output", str(out),
    ])
    assert result.exit_code == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["adapter"] == "gold-passthrough"


def test_compare_two_adapters():
    runner = CliRunner()
    result = runner.invoke(cli, [
        "compare", str(FIXTURES_DIR), "--adapters", "passthrough,majority",
    ])
    assert result.exit_code == 0
    assert "Head-to-Head" in result.output
    assert "gold-passthrough" in result.output
    assert "majority-class" in result.output


def test_compare_with_output(tmp_path):
    import json

    runner = CliRunner()
    out = tmp_path / "comparison.json"
    result = runner.invoke(cli, [
        "compare", str(FIXTURES_DIR), "--adapters", "passthrough,majority",
        "--output", str(out),
    ])
    assert result.exit_code == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert len(data["adapters"]) == 2


def test_evaluate_unknown_adapter():
    runner = CliRunner()
    result = runner.invoke(cli, [
        "evaluate", str(FIXTURES_DIR), "--adapter", "nonexistent",
    ])
    assert result.exit_code != 0


class TestDocumentSelection:
    """--documents pins the evaluated set; --subset only samples it."""

    def test_evaluate_named_document(self):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "evaluate", str(FIXTURES_DIR), "--adapter", "passthrough",
            "--documents", "T001",
        ])
        assert result.exit_code == 0
        assert "Documents selected" in result.output

    def test_unknown_document_id_fails_clearly(self):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "evaluate", str(FIXTURES_DIR), "--adapter", "passthrough",
            "--documents", "T001,NOSUCHDOC",
        ])
        assert result.exit_code != 0
        assert "not in corpus" in result.output

    def test_documents_and_subset_are_mutually_exclusive(self):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "evaluate", str(FIXTURES_DIR), "--adapter", "passthrough",
            "--documents", "T001", "--subset", "1",
        ])
        assert result.exit_code != 0
        assert "mutually exclusive" in result.output

    def test_subset_prints_pinned_equivalent(self):
        """A sampled run should tell you how to repeat it exactly."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "evaluate", str(FIXTURES_DIR), "--adapter", "passthrough", "--subset", "1",
        ])
        assert result.exit_code == 0
        assert "--documents T001" in result.output

    def test_saved_json_records_document_ids(self, tmp_path):
        import json

        out = tmp_path / "result.json"
        runner = CliRunner()
        result = runner.invoke(cli, [
            "evaluate", str(FIXTURES_DIR), "--adapter", "passthrough",
            "--documents", "T001", "--output", str(out),
        ])
        assert result.exit_code == 0
        assert json.loads(out.read_text())["document_ids"] == ["T001"]

    def test_compare_accepts_documents(self):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "compare", str(FIXTURES_DIR), "--adapters", "passthrough,majority",
            "--documents", "T001",
        ])
        assert result.exit_code == 0
        assert "Head-to-Head" in result.output


class TestChunkSize:
    def test_chunk_size_reaches_the_adapter(self, tmp_path, monkeypatch):
        captured = {}

        class FakeAdapter:
            name = "fake"

            def __init__(self, **kwargs):
                captured.update(kwargs)

            def predict(self, document):
                return [t.pos_mhdbdb for t in document.mappable_tokens]

        monkeypatch.setattr(
            "mhd_pos_benchmark.adapters.generic_cli.GenericCliAdapter", FakeAdapter
        )
        runner = CliRunner()
        result = runner.invoke(cli, [
            "evaluate", str(FIXTURES_DIR), "--adapter", "cli",
            "--cli-cmd", "fake -p", "--chunk-size", "500",
        ])
        assert result.exit_code == 0, result.output
        assert captured["chunk_size"] == 500

    def test_chunk_size_omitted_leaves_adapter_default(self, tmp_path, monkeypatch):
        captured = {}

        class FakeAdapter:
            name = "fake"

            def __init__(self, **kwargs):
                captured.update(kwargs)

            def predict(self, document):
                return [t.pos_mhdbdb for t in document.mappable_tokens]

        monkeypatch.setattr(
            "mhd_pos_benchmark.adapters.generic_cli.GenericCliAdapter", FakeAdapter
        )
        runner = CliRunner()
        result = runner.invoke(cli, [
            "evaluate", str(FIXTURES_DIR), "--adapter", "cli", "--cli-cmd", "fake -p",
        ])
        assert result.exit_code == 0, result.output
        assert "chunk_size" not in captured


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
