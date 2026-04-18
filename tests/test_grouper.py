"""Tests for grouper and summary modules."""
import textwrap
import pytest

from stacktrace_filter.grouper import group, TracebackGroup
from stacktrace_filter.summary import render_summary

LOG_TWO_ERRORS = textwrap.dedent("""\
    Traceback (most recent call last):
      File "app.py", line 10, in run
        do_thing()
      File "lib.py", line 5, in do_thing
        raise ValueError("bad value")
    ValueError: bad value

    Some log line in between

    Traceback (most recent call last):
      File "app.py", line 20, in handle
        fetch()
      File "net.py", line 3, in fetch
        raise KeyError("missing")
    KeyError: missing
""")

LOG_SAME_ERROR_TWICE = textwrap.dedent("""\
    Traceback (most recent call last):
      File "a.py", line 1, in f
        boom()
    RuntimeError: boom

    Traceback (most recent call last):
      File "b.py", line 2, in g
        boom()
    RuntimeError: boom
""")


def test_group_count():
    g = group(LOG_TWO_ERRORS)
    assert g.count == 2


def test_group_exception_types():
    g = group(LOG_TWO_ERRORS)
    assert g.exception_types == ["ValueError", "KeyError"]


def test_unique_exceptions():
    g = group(LOG_SAME_ERROR_TWICE)
    assert g.unique_exceptions() == ["RuntimeError"]


def test_filter_by_exception():
    g = group(LOG_TWO_ERRORS)
    sub = g.filter_by_exception("ValueError")
    assert sub.count == 1
    assert sub.exception_types == ["ValueError"]


def test_empty_group():
    g = group("nothing here")
    assert g.count == 0
    assert g.unique_exceptions() == []


def test_summary_contains_total():
    g = group(LOG_TWO_ERRORS)
    out = render_summary(g, color=False)
    assert "2" in out
    assert "Traceback Summary" in out


def test_summary_lists_exception_types():
    g = group(LOG_TWO_ERRORS)
    out = render_summary(g, color=False)
    assert "ValueError" in out
    assert "KeyError" in out


def test_summary_empty_group():
    g = TracebackGroup()
    out = render_summary(g, color=False)
    assert "No tracebacks" in out
