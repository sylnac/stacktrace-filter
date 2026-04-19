"""Tests for snapshot CLI commands."""
import json
from pathlib import Path

import pytest

from stacktrace_filter.snapshot_cli import build_snapshot_parser, main

TRACEBACK_TEXT = """Traceback (most recent call last):
  File \"app/main.py\", line 5, in run
    do_thing()
ValueError: something went wrong
"""


@pytest.fixture()
def log_file(tmp_path) -> Path:
    p = tmp_path / "app.log"
    p.write_text(TRACEBACK_TEXT)
    return p


def test_build_parser_has_subcommands():
    p = build_snapshot_parser()
    assert p is not None


def test_save_creates_snapshot(log_file, tmp_path):
    out = tmp_path / "snap.json"
    main(["save", str(log_file), str(out)])
    assert out.exists()
    data = json.loads(out.read_text())
    assert "tracebacks" in data


def test_save_uses_label(log_file, tmp_path):
    out = tmp_path / "snap.json"
    main(["save", str(log_file), str(out), "--label", "my-run"])
    data = json.loads(out.read_text())
    assert data["label"] == "my-run"


def test_save_missing_file_exits(tmp_path):
    out = tmp_path / "snap.json"
    with pytest.raises(SystemExit):
        main(["save", str(tmp_path / "nope.log"), str(out)])


def test_diff_output(log_file, tmp_path, capsys):
    snap1 = tmp_path / "s1.json"
    snap2 = tmp_path / "s2.json"
    main(["save", str(log_file), str(snap1), "--label", "run-1"])
    main(["save", str(log_file), str(snap2), "--label", "run-2"])
    main(["diff", str(snap1), str(snap2)])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["old_label"] == "run-1"
    assert data["new_label"] == "run-2"


def test_diff_missing_file_exits(tmp_path, log_file):
    snap1 = tmp_path / "s1.json"
    main(["save", str(log_file), str(snap1)])
    with pytest.raises(SystemExit):
        main(["diff", str(snap1), str(tmp_path / "missing.json")])
