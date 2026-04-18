"""Tests for stacktrace_filter.formatter."""

import pytest

from stacktrace_filter.parser import parse
from stacktrace_filter.formatter import format_traceback, FormatOptions

SAMPLE = """\
Traceback (most recent call last):
  File "/usr/lib/python3.11/threading.py", line 1038, in _bootstrap
    self._bootstrap_inner()
  File "/home/user/project/app/worker.py", line 42, in run
    result = process(task)
  File "/home/user/project/app/core.py", line 17, in process
    raise ValueError("bad input")
ValueError: bad input
"""


@pytest.fixture
def tb():
    tracebacks = parse(SAMPLE)
    assert tracebacks
    return tracebacks[0]


def test_format_contains_exception(tb):
    out = format_traceback(tb, FormatOptions(color=False))
    assert "ValueError: bad input" in out


def test_format_contains_header(tb):
    out = format_traceback(tb, FormatOptions(color=False))
    assert "Traceback (most recent call last):" in out


def test_collapse_stdlib_hides_frame(tb):
    opts = FormatOptions(color=False, collapse_stdlib=True)
    out = format_traceback(tb, opts)
    assert "threading.py" not in out
    assert "collapsed" in out


def test_no_collapse_shows_all_frames(tb):
    opts = FormatOptions(color=False, collapse_stdlib=False, collapse_site_packages=False)
    out = format_traceback(tb, opts)
    assert "threading.py" in out
    assert "worker.py" in out
    assert "core.py" in out


def test_collapse_label_stdlib(tb):
    opts = FormatOptions(color=False, collapse_stdlib=True)
    out = format_traceback(tb, opts)
    assert "stdlib" in out


def test_color_output_contains_ansi(tb):
    opts = FormatOptions(color=True, collapse_stdlib=False)
    out = format_traceback(tb, opts)
    assert "\033[" in out


def test_no_color_output_lacks_ansi(tb):
    opts = FormatOptions(color=False)
    out = format_traceback(tb, opts)
    assert "\033[" not in out


def test_origin_note_present(tb):
    opts = FormatOptions(color=False, collapse_stdlib=False)
    out = format_traceback(tb, opts)
    assert "origin:" in out
