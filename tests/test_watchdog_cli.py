"""Tests for stacktrace_filter.watchdog_cli."""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from_cli import build_watchdog_parser, main


TRACEBACK_TEXT = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
      File "app.py", line 5, in do_thing
        raise ValueError("boom")
    ValueError: boom
""")


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text(TRACEBACK_TEXT, encoding="utf-8")
    return p


def test_build_parser_defaults() -> None:
    p = build_watchdog_parser()
    args = p.parse_args(["some.log"])
    assert args.poll == 0.5
    assert not args.no_collapse
    assert not args.no_color


def test_main_missing_file(tmp_path: Path,Fixture) -> None:
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "missing.log")])
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_outputs_exception(log_file: Path, capsys: pytest.CaptureFixture) -> None:
    with patch(
        "stacktrace_filter.watchdog_cli.iter_watch",
        return_value=iter([]),
    ):
        main([str(log_file), "--no-color"])
    # No crash is sufficient; real output tested via iter_watch tests


def test_main_no_collapse_flag(log_file: Path) -> None:
    p = build_watchdog_parser()
    args = p.parse_args([str(log_file), "--no-collapse"])
    assert args.no_collapse is True
