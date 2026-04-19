import pytest
from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.differ import diff_tracebacks, FrameDiff


def _frame(fn, lineno=10, filename="app.py"):
    return Frame(filename=filename, lineno=lineno, function=fn, context="pass")


def _tb(frames, exc_type="ValueError", exc_msg="oops"):
    return Traceback(frames=frames, exc_type=exc_type, exc_message=exc_msg, raw="")


def test_identical_tracebacks():
    f = _frame("main")
    d = diff_tracebacks(_tb([f]), _tb([f]))
    assert d.is_identical
    assert d.divergence_index is None


def test_changed_frame_detected():
    left = _tb([_frame("a"), _frame("b", lineno=1)])
    right = _tb([_frame("a"), _frame("b", lineno=99)])
    d = diff_tracebacks(left, right)
    assert not d.is_identical
    assert d.divergence_index == 1
    assert d.frame_diffs[1].status == "changed"


def test_left_only_frame():
    left = _tb([_frame("a"), _frame("b")])
    right = _tb([_frame("a")])
    d = diff_tracebacks(left, right)
    assert d.frame_diffs[1].status == "left_only"


def test_right_only_frame():
    left = _tb([_frame("a")])
    right = _tb([_frame("a"), _frame("c")])
    d = diff_tracebacks(left, right)
    assert d.frame_diffs[1].status == "right_only"


def test_different_exception_not_identical():
    f = _frame("main")
    left = _tb([f], exc_type="ValueError")
    right = _tb([f], exc_type="TypeError")
    d = diff_tracebacks(left, right)
    assert not d.is_identical
    assert not d.same_exception


def test_equal_frames_status():
    f = _frame("run")
    d = diff_tracebacks(_tb([f]), _tb([f]))
    assert all(fd.status == "equal" for fd in d.frame_diffs)
