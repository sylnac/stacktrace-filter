"""Tests for stacktrace_filter.throttle_cli."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from stacktrace_filter.throttle_cli import build_throttle_parser, main

LOG = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 5, in run
        boom()
    ValueError: something went wrong
""")


@pytest.fixture()
def log_file(tmp_path):
    f = tmp_path / "run.log"
    f.write_text(LOG)
    return f


def test_build_parser_defaults():
    p = build_throttle_parser()
    args = p.parse_args([])
    assert args.window == 60.0
    assert args.max_per_window == 3
    assert args.no_collapse is False


def test_main_missing_file_exits():
    with pytest.raises(SystemExit):
        main(["nonexistent_file.log"])


def test_main_reads_file(log_file, capsys):
    main([str(log_file)])
    out = capsys.readouterr().out
    assert "ValueError" in out


def test_main_no_collapse_flag(log_file, capsys):
    main([str(log_file), "--no-collapse"])
    out = capsys.readouterr().out
    assert "ValueError" in out


def test_main_suppresses_repeats(tmp_path, capsys):
    # Write a log with the same traceback repeated 5 times
    log = tmp_path / "rep.log"
    log.write_text(LOG * 5)
    main([str(log), "--max", "2"])
    out = capsys.readouterr().out
    assert out.count("ValueError") <= 2
