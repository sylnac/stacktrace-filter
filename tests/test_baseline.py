"""Tests for stacktrace_filter.baseline."""
from __future__ import annotations

from stacktrace_filter.parser import Frame, Traceback
from stacktrace_filter.snapshot import Snapshot
from stacktrace_filter.baseline import compare, render_baseline_report, _exc_key


def _frame(filename="app.py", lineno=10, name="fn", line="x()"):
    return Frame(filename=filename, lineno=lineno, name=name, line=line)


def _tb(exc_type="ValueError", exc_message="bad", filename="app.py", lineno=10):
    return Traceback(
        frames=[_frame(filename=filename, lineno=lineno)],
        exc_type=exc_type,
        exc_message=exc_message,
    )


def _snapshot(*tbs):
    return Snapshot(label="base", tracebacks=list(tbs))


def test_exc_key_uses_type_and_location():
    tb = _tb(exc_type="KeyError", filename="mod.py", lineno=42)
    assert _exc_key(tb) == "KeyError@mod.py:42"


def test_new_exception_detected():
    current = [_tb(exc_type="RuntimeError", lineno=99)]
    snap = _snapshot(_tb(exc_type="ValueError", lineno=10))
    result = compare(current, snap)
    assert len(result.new) == 1
    assert result.new[0].exc_type == "RuntimeError"


def test_recurring_exception_detected():
    tb = _tb()
    result = compare([tb], _snapshot(tb))
    assert len(result.recurring) == 1
    assert len(result.new) == 0


def test_resolved_exception_detected():
    old = _tb(exc_type="OldError", lineno=5)
    snap = _snapshot(old)
    result = compare([], snap)
    assert len(result.resolved) == 1
    assert result.resolved[0].exc_type == "OldError"


def test_has_regressions_true():
    result = compare([_tb(lineno=99)], _snapshot(_tb(lineno=10)))
    assert result.has_regressions is True


def test_has_regressions_false():
    tb = _tb()
    result = compare([tb], _snapshot(tb))
    assert result.has_regressions is False


def test_render_contains_counts():
    tb_new = _tb(exc_type="NewError", lineno=99)
    tb_old = _tb(exc_type="OldError", lineno=10)
    snap = _snapshot(tb_old)
    result = compare([tb_new], snap)
    report = render_baseline_report(result)
    assert "New (regressions) : 1" in report
    assert "Resolved          : 1" in report


def test_render_lists_new_exceptions():
    tb = _tb(exc_type="BoomError", exc_message="boom", lineno=77)
    result = compare([tb], _snapshot())
    report = render_baseline_report(result)
    assert "BoomError" in report
    assert "boom" in report
