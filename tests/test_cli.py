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


def test_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
