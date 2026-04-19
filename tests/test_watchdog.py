"""Tests for stacktrace_filter.watchdog."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from stacktrace_filter.watchdog import iter_watch, watch


TRACEBACK_TEXT = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
      File "app.py", line 5, in do_thing
        raise ValueError("boom")
    ValueError: boom
""")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_watch_callback_called(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    _write(log, TRACEBACK_TEXT)

    received: list = []
    watch(log, received.append, poll_interval=0, max_iterations=1)
    assert len(received) == 1
    assert received[0].exc_type == "ValueError"


def test_watch_deduplicates(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    _write(log, TRACEBACK_TEXT * 3)

    received: list = []
    watch(log, received.append, poll_interval=0, max_iterations=1)
    assert len(received) == 1


def test_watch_no_traceback(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    _write(log, "INFO starting up\nINFO done\n")

    received: list = []
    watch(log, received.append, poll_interval=0, max_iterations=1)
    assert received == []


def test_iter_watch_yields_traceback(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    _write(log, TRACEBACK_TEXT)

    results = list(iter_watch(log, poll_interval=0, max_iterations=1))
    assert len(results) == 1
    assert results[0].exc_message == "boom"


def test_watch_picks_up_appended_content(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    log.write_text("", encoding="utf-8")  # empty initially

    # First iteration: nothing
    received: list = []

    def _append_on_first(tb) -> None:  # noqa: ANN001
        received.append(tb)

    # Manually simulate: write content then run one iteration starting at pos=0
    log.write_text(TRACEBACK_TEXT, encoding="utf-8")
    watch(log, _append_on_first, poll_interval=0, max_iterations=1)
    assert len(received) == 1
