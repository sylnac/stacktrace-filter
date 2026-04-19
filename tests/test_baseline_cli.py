"""Tests for stacktrace_filter.baseline_cli."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from stacktrace_filter.baseline_cli import build_baseline_parser, main


TRACEBACK_TEXT = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
    ValueError: something went wrong
""")


@pytest.fixture()
def snapshot_file(tmp_path):
    snap = {
        "label": "base",
        "created_at": "2024-01-01T00:00:00",
        "tracebacks": [],
    }
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(snap))
    return p


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "run.log"
    p.write_text(TRACEBACK_TEXT)
    return p


def test_build_parser_has_snapshot_arg():
    p = build_baseline_parser()
    args = p.parse_args(["snap.json"])
    assert args.snapshot == "snap.json"


def test_build_parser_fail_on_regression_default():
    p = build_baseline_parser()
    args = p.parse_args(["snap.json"])
    assert args.fail_on_regression is False


def test_main_outputs_report(snapshot_file, log_file, capsys):
    main([str(snapshot_file), str(log_file)])
    out = capsys.readouterr().out
    assert "Baseline comparison" in out


def test_main_missing_snapshot_exits(tmp_path, log_file):
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "missing.json"), str(log_file)])
    assert exc.value.code == 1


def test_main_missing_log_exits(snapshot_file, tmp_path):
    with pytest.raises(SystemExit) as exc:
        main([str(snapshot_file), str(tmp_path / "nope.log")])
    assert exc.value.code == 1


def test_main_fail_on_regression(snapshot_file, log_file):
    with pytest.raises(SystemExit) as exc:
        main(["--fail-on-regression", str(snapshot_file), str(log_file)])
    assert exc.value.code == 1
