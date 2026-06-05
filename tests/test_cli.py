"""CLI smoke tests."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli import app
from src.config import reset_settings_cache

runner = CliRunner()


def test_cli_help() -> None:
    reset_settings_cache()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "process" in result.stdout
    assert "draft" in result.stdout


def test_cli_info() -> None:
    reset_settings_cache()
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "Ambitio Doc AI" in result.stdout


def test_cli_process_empty_directory(tmp_path: Path) -> None:
    reset_settings_cache()
    input_dir = tmp_path / "samples"
    input_dir.mkdir()
    result = runner.invoke(app, ["process", "--input", str(input_dir)])
    assert result.exit_code == 0
    assert "Processed 0 document(s)" in result.stdout
