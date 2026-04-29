"""Tests for stacktrace_filter.suppressor_cli."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from stacktrace_filter.suppressor_cli import build_suppressor_parser, main

_TRACEBACK = textwrap.dedent("""\
    Traceback (most recent call last):
      File "/app/main.py", line 10, in run
        raise ValueError("bad input")
    ValueError: bad input
""")

_TWO_TRACEBACKS = _TRACEBACK + "\n" + textwrap.dedent("""\
    Traceback (most recent call last):
      File "/app/main.py", line 20, in handle
        raise KeyError("missing key")
    KeyError: missing key
""")


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    f = tmp_path / "app.log"
    f.write_text(_TWO_TRACEBACKS)
    return f


def test_build_parser_defaults():
    p = build_suppressor_parser()
    args = p.parse_args([])
    assert args.suppress_types == []
    assert args.suppress_messages == []
    assert args.min_frames == 1
    assert args.deduplicate is False
    assert args.no_collapse is False


def test_main_missing_file_exits():
    with pytest.raises(SystemExit):
        main(["nonexistent_file.log"])


def test_main_reads_file(log_file: Path, capsys):
    main([str(log_file)])
    out = capsys.readouterr().out
    assert "ValueError" in out or "KeyError" in out


def test_main_suppress_type_filters(log_file: Path, capsys):
    main([str(log_file), "--suppress-type", "KeyError"])
    out = capsys.readouterr().out
    assert "KeyError" not in out or "suppressed" in out
    assert "ValueError" in out


def test_main_summary_line_present(log_file: Path, capsys):
    main([str(log_file)])
    out = capsys.readouterr().out
    assert "suppressor:" in out


def test_main_no_collapse_flag(log_file: Path, capsys):
    main([str(log_file), "--no-collapse"])
    out = capsys.readouterr().out
    assert "ValueError" in out or "KeyError" in out


def test_main_deduplicate_suppresses_duplicates(tmp_path: Path, capsys):
    f = tmp_path / "dup.log"
    f.write_text(_TRACEBACK + "\n" + _TRACEBACK)
    main([str(f), "--deduplicate"])
    out = capsys.readouterr().out
    assert "suppressed 1" in out
