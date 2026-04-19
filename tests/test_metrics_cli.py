"""Tests for the metrics CLI entry point."""

import json
from pathlib import Path

import pytest

from stacktrace_filter.metrics_cli import build_metrics_parser, main


@pytest.fixture
def log_file(tmp_path):
    content = """Traceback (most recent call last):
  File "app.py", line 10, in run
    do_thing()
  File "app.py", line 20, in do_thing
    raise ValueError("bad input")
ValueError: bad input

Traceback (most recent call last):
  File "app.py", line 10, in run
    do_thing()
  File "app.py", line 20, in do_thing
    raise KeyError("missing key")
KeyError: missing key

Traceback (most recent call last):
  File "app.py", line 10, in run
    do_thing()
  File "app.py", line 20, in do_thing
    raise ValueError("another bad input")
ValueError: another bad input
"""
    p = tmp_path / "app.log"
    p.write_text(content)
    return p


def test_build_parser_defaults():
    parser = build_metrics_parser()
    args = parser.parse_args(["somefile.log"])
    assert args.file == "somefile.log"
    assert args.format == "text"


def test_build_parser_json_format():
    parser = build_metrics_parser()
    args = parser.parse_args(["somefile.log", "--format", "json"])
    assert args.format == "json"


def test_main_missing_file_exits(tmp_path):
    missing = str(tmp_path / "no.log")
    with pytest.raises(SystemExit):
        main([missing])


def test_main_outputs_report(log_file, capsys):
    main([str(log_file)])
    out = capsys.readouterr().out
    assert "ValueError" in out or "KeyError" in out


def test_main_total_count(log_file, capsys):
    main([str(log_file)])
    out = capsys.readouterr().out
    # 3 tracebacks total
    assert "3" in out


def test_main_json_format(log_file, capsys):
    main([str(log_file), "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "total" in data
    assert data["total"] == 3


def test_main_json_by_exception(log_file, capsys):
    main([str(log_file), "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "by_exception" in data
    assert data["by_exception"].get("ValueError", 0) == 2
    assert data["by_exception"].get("KeyError", 0) == 1
