import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.differ import diff_tracebacks
from stacktrace_filter.diff_formatter import format_diff


def _frame(fn, lineno=10):
    return Frame(filename="app.py", lineno=lineno, function=fn, context="pass")


def _tb(frames, exc_type="ValueError", msg="bad"):
    return Traceback(frames=frames, exc_type=exc_type, exc_message=msg, raw="")


def test_format_identical_says_identical():
    f = _frame("main")
    d = diff_tracebacks(_tb([f]), _tb([f]))
    out = format_diff(d, colour=False)
    assert "identical" in out.lower()


def test_format_shows_divergence_index():
    left = _tb([_frame("a"), _frame("b", lineno=1)])
    right = _tb([_frame("a"), _frame("b", lineno=2)])
    d = diff_tracebacks(left, right)
    out = format_diff(d, colour=False)
    assert "1" in out


def test_format_contains_header():
    f = _frame("x")
    d = diff_tracebacks(_tb([f]), _tb([f]))
    out = format_diff(d, colour=False)
    assert "Traceback Diff" in out


def test_format_diff_exception_lines():
    f = _frame("x")
    left = _tb([f], exc_type="ValueError", msg="a")
    right = _tb([f], exc_type="TypeError", msg="b")
    d = diff_tracebacks(left, right)
    out = format_diff(d, colour=False)
    assert "ValueError" in out
    assert "TypeError" in out


def test_format_no_colour_no_escape_codes():
    f = _frame("run")
    d = diff_tracebacks(_tb([f, _frame("sub", 20)]), _tb([f]))
    out = format_diff(d, colour=False)
    assert "\033[" not in out
