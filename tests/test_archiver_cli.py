"""Tests for stacktrace_filter.archiver_cli."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from stacktrace_filter.archiver_cli import build_archiver_parser, main

TRACEBACK_TEXT = """\
Traceback (most recent call last):
  File "app/run.py", line 5, in go
    raise KeyError('missing')
KeyError: 'missing'
"""


@pytest.fixture()
def log_file(tmp_path) -> Path:
    f = tmp_path / "app.log"
    f.write_text(TRACEBACK_TEXT, encoding="utf-8")
    return f


def test_build_parser_has_subcommands():
    p = build_archiver_parser()
    assert p is not None


def test_save_creates_archive(tmp_path, log_file):
    arc_dir = tmp_path / "arc"
    main(["save", str(log_file), "--dir", str(arc_dir)])
    files = list(arc_dir.glob("archive-*.jsonl"))
    assert len(files) == 1


def test_save_prints_count(tmp_path, log_file, capsys):
    arc_dir = tmp_path / "arc"
    main(["save", str(log_file), "--dir", str(arc_dir)])
    out = capsys.readouterr().out
    assert "1 traceback" in out


def test_save_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit):
        main(["save", str(tmp_path / "nope.log"), "--dir", str(tmp_path / "arc")])


def test_save_custom_label(tmp_path, log_file):
    arc_dir = tmp_path / "arc"
    main(["save", str(log_file), "--dir", str(arc_dir), "--label", "prod"])
    files = list(arc_dir.glob("prod-*.jsonl"))
    assert len(files) == 1


def test_show_prints_exception(tmp_path, log_file, capsys):
    arc_dir = tmp_path / "arc"
    main(["save", str(log_file), "--dir", str(arc_dir)])
    archive_file = sorted(arc_dir.glob("archive-*.jsonl"))[0]
    main(["show", str(archive_file)])
    out = capsys.readouterr().out
    assert "KeyError" in out


def test_show_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit):
        main(["show", str(tmp_path / "missing.jsonl")])
