"""Tests for stacktrace_filter.correlator_cli."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from stacktrace_filter.correlator_cli import build_correlator_parser, main


TRACEBACK_TEXT = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        result = compute()
    ValueError: bad input
""")


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    f = tmp_path / "app.log"
    f.write_text(TRACEBACK_TEXT)
    return f


def test_build_parser_has_files_arg():
    p = build_correlator_parser()
    args = p.parse_args(["a.log", "b.log"])
    assert args.files == ["a.log", "b.log"]


def test_build_parser_defaults():
    p = build_correlator_parser()
    args = p.parse_args(["a.log"])
    assert args.top == 0
    assert args.no_color is False
    assert args.output is None


def test_main_missing_file_exits():
    rc = main(["nonexistent_file_xyz.log"])
    assert rc == 2


def test_main_reads_file(log_file: Path, capsys: pytest.CaptureFixture):
    rc = main([str(log_file), "--no-color"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Correlation Report" in captured.out


def test_main_outputs_exception(log_file: Path, capsys: pytest.CaptureFixture):
    rc = main([str(log_file), "--no-color"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "ValueError" in captured.out


def test_main_top_flag(log_file: Path, capsys: pytest.CaptureFixture):
    rc = main([str(log_file), "--top", "1", "--no-color"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Correlation Report" in captured.out


def test_main_writes_output_file(log_file: Path, tmp_path: Path):
    out = tmp_path / "result.txt"
    rc = main([str(log_file), "--no-color", "--output", str(out)])
    assert rc == 0
    assert out.exists()
    assert "Correlation Report" in out.read_text()
